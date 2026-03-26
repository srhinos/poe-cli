"""Crafting simulation engine using CoE data."""

from __future__ import annotations

import contextlib
import random
from dataclasses import dataclass, field

from .craftdata import CraftData


@dataclass
class RolledMod:
    """A mod rolled onto an item."""

    mod_id: str
    name: str
    affix: str  # "prefix" or "suffix"
    modgroup: str
    weight: int
    chance: float  # probability this mod was selected from the pool
    tier: dict  # tier data: ilvl, values, weight
    rolls: list  # actual rolled values


@dataclass
class CraftableItem:
    """An item being crafted."""

    base_name: str
    base_id: str
    ilvl: int
    influences: list[str] = field(default_factory=list)
    rarity: str = "rare"  # "normal", "magic", "rare"
    prefixes: list[RolledMod] = field(default_factory=list)
    suffixes: list[RolledMod] = field(default_factory=list)
    max_prefixes: int = 3
    max_suffixes: int = 3
    # Metamods
    prefixes_locked: bool = False  # "Prefixes Cannot Be Changed"
    suffixes_locked: bool = False  # "Suffixes Cannot Be Changed"

    @property
    def all_mods(self) -> list[RolledMod]:
        return self.prefixes + self.suffixes

    @property
    def open_prefixes(self) -> int:
        return self.max_prefixes - len(self.prefixes)

    @property
    def open_suffixes(self) -> int:
        return self.max_suffixes - len(self.suffixes)

    @property
    def modgroups(self) -> set[str]:
        return {m.modgroup for m in self.all_mods}


@dataclass
class SimResult:
    """Results from a crafting simulation."""

    method: str
    iterations: int
    hits: int
    hit_rate: float
    avg_attempts: float
    avg_cost_chaos: float
    cost_per_attempt: float
    percentiles: dict[str, int]  # "p50", "p75", "p90", "p99" -> attempts


class CraftingEngine:
    """Simulates PoE crafting using CoE mod pool data."""

    def __init__(self, data: CraftData) -> None:
        self.data = data

    def create_item(
        self,
        base: str,
        ilvl: int = 84,
        influences: list[str] | None = None,
    ) -> CraftableItem:
        """Create a blank craftable item."""
        bitem = self.data.get_base_item(base)
        if not bitem:
            raise ValueError(f"Unknown base item: {base}")

        base_id = bitem["id_base"]
        bg = self.data.get_base_group(base_id)

        max_affixes = int(bg["max_affix"]) if bg else 6
        max_p = max_affixes // 2
        max_s = max_affixes - max_p

        return CraftableItem(
            base_name=base,
            base_id=base_id,
            ilvl=ilvl,
            influences=influences or [],
            max_prefixes=max_p,
            max_suffixes=max_s,
        )

    def _build_mod_pool(
        self,
        item: CraftableItem,
        affix_type: str | None = None,
        fossil_weights: dict[str, float] | None = None,
    ) -> list[dict]:
        """Build the weighted mod pool for an item, respecting current mods."""
        all_mods = self.data.get_mod_pool(
            item.base_name,
            ilvl=item.ilvl,
            influences=item.influences,
        )

        existing_groups = item.modgroups
        pool = []

        for mod in all_mods:
            # Skip if mod group already on item
            if mod["modgroup"] in existing_groups:
                continue

            affix = mod["affix"]

            # Filter by affix type
            if affix_type and affix != affix_type:
                continue

            # Check slot availability
            if affix == "prefix" and item.open_prefixes <= 0:
                continue
            if affix == "suffix" and item.open_suffixes <= 0:
                continue

            weight = mod["weight"]

            # Apply fossil weight modifiers
            if fossil_weights and mod.get("mtypes"):
                multiplier = 1.0
                for mtype_id in mod["mtypes"]:
                    if mtype_id in fossil_weights:
                        multiplier += fossil_weights[mtype_id]
                weight = int(weight * max(multiplier, 0))

            if weight <= 0:
                continue

            pool.append({**mod, "weight": weight})

        return pool

    def _weighted_pick(self, pool: list[dict]) -> dict | None:
        """Weighted random selection from mod pool."""
        if not pool:
            return None
        total = sum(m["weight"] for m in pool)
        if total <= 0:
            return None
        r = random.randint(1, total)
        cumulative = 0
        for mod in pool:
            cumulative += mod["weight"]
            if r <= cumulative:
                return mod
        return pool[-1]

    def _roll_values(self, tier: dict) -> list:
        """Roll random values within tier ranges."""
        values = tier.get("values", [])
        rolled = []
        for v in values:
            if isinstance(v, list) and len(v) == 2:
                rolled.append(random.uniform(v[0], v[1]))
            else:
                rolled.append(v)
        return rolled

    def _add_mod(self, item: CraftableItem, mod: dict, pool_total: int = 0) -> RolledMod:
        """Roll and add a mod to the item."""
        chance = mod["weight"] / pool_total if pool_total > 0 else 0

        rolled = RolledMod(
            mod_id=mod["mod_id"],
            name=mod["name"],
            affix=mod["affix"],
            modgroup=mod["modgroup"],
            weight=mod["weight"],
            chance=chance,
            tier=mod["best_tier"],
            rolls=self._roll_values(mod["best_tier"]),
        )

        if mod["affix"] == "prefix":
            item.prefixes.append(rolled)
        else:
            item.suffixes.append(rolled)

        return rolled

    def _get_fossil_weights(self, fossil_names: list[str]) -> dict[str, float]:
        """Get combined fossil weight modifiers by mtype_id."""
        fossils = self.data.get_fossils()
        weights: dict[str, float] = {}

        d = self.data._main()
        mtypes_by_name = {m["name_mtype"].lower(): m["id_mtype"] for m in d["mtypes"]["seq"]}

        for fossil in fossils:
            if fossil["name"] not in fossil_names:
                continue
            mod_data = fossil.get("mod_weights", {})
            for tag_name, w in mod_data.items():
                mtype_id = mtypes_by_name.get(tag_name.lower())
                if mtype_id:
                    # Additive stacking (CoE's poec_cFosMode == "a")
                    weights[mtype_id] = weights.get(mtype_id, 0) + (w / 1000.0)

        return weights

    # ── crafting operations ───────────────────────────────────────────────

    def _roll_item(
        self, item: CraftableItem, num_mods: int, fossil_weights: dict[str, float] | None = None
    ) -> None:
        """Fast inner roll: populate an item with num_mods random mods."""
        item.prefixes.clear()
        item.suffixes.clear()
        for _ in range(num_mods):
            pool = self._build_mod_pool(item, fossil_weights=fossil_weights)
            picked = self._weighted_pick(pool)
            if picked:
                self._add_mod(item, picked)

    def chaos_roll(self, item: CraftableItem) -> None:
        """Chaos Orb: reroll all mods as rare (4-6 mods)."""
        item.rarity = "rare"
        self._roll_item(item, random.randint(4, 6))

    def alt_roll(self, item: CraftableItem) -> None:
        """Alteration: reroll as magic (1-2 mods)."""
        item.rarity = "magic"
        self._roll_item(item, random.randint(1, 2))

    def regal(self, item: CraftableItem) -> RolledMod | None:
        """Regal: upgrade magic to rare, adding one mod."""
        if item.rarity != "magic":
            return None
        item.rarity = "rare"
        pool = self._build_mod_pool(item)
        picked = self._weighted_pick(pool)
        if picked:
            total = sum(m["weight"] for m in pool)
            return self._add_mod(item, picked, pool_total=total)
        return None

    def exalt(self, item: CraftableItem) -> RolledMod | None:
        """Exalted Orb: add one random mod to a rare item."""
        if item.rarity != "rare":
            return None
        pool = self._build_mod_pool(item)
        picked = self._weighted_pick(pool)
        if picked:
            total = sum(m["weight"] for m in pool)
            return self._add_mod(item, picked, pool_total=total)
        return None

    def annul(self, item: CraftableItem) -> RolledMod | None:
        """Orb of Annulment: remove a random mod."""
        all_mods = item.all_mods
        if not all_mods:
            return None

        # Respect metamods
        removable = []
        if not item.prefixes_locked:
            removable.extend(item.prefixes)
        if not item.suffixes_locked:
            removable.extend(item.suffixes)

        if not removable:
            return None

        removed = random.choice(removable)
        if removed in item.prefixes:
            item.prefixes.remove(removed)
        else:
            item.suffixes.remove(removed)
        return removed

    def scour(self, item: CraftableItem) -> None:
        """Orb of Scouring: remove all mods (respects metamods)."""
        if item.prefixes_locked and item.suffixes_locked:
            return
        if not item.prefixes_locked:
            item.prefixes.clear()
        if not item.suffixes_locked:
            item.suffixes.clear()
        if not item.all_mods:
            item.rarity = "normal"

    def essence_roll(self, item: CraftableItem, essence_name: str) -> None:
        """Essence: reroll as rare, guaranteeing a specific mod."""
        item.rarity = "rare"
        self._roll_item(item, random.randint(4, 6))

    def fossil_roll(self, item: CraftableItem, fossil_names: list[str]) -> None:
        """Fossil: reroll as rare with modified weights."""
        item.rarity = "rare"
        fossil_weights = self._get_fossil_weights(fossil_names)
        self._roll_item(item, random.randint(4, 6), fossil_weights=fossil_weights)

    # ── simulation ────────────────────────────────────────────────────────

    def simulate(
        self,
        base: str,
        ilvl: int,
        method: str,
        target_mods: list[str],
        iterations: int = 10000,
        influences: list[str] | None = None,
        fossils: list[str] | None = None,
        match_mode: str = "all",
        max_attempts: int = 10000,
    ) -> SimResult:
        """Run a crafting simulation.

        target_mods: list of mod group names to hit (e.g. ["IncreasedLife", "ColdResistance"])
        match_mode: "all" (all targets present) or "any" (at least one)
        max_attempts: maximum attempts per iteration before giving up
        """
        target_set = {t.lower() for t in target_mods}
        hits = 0
        attempts_on_hit: list[int] = []

        fossil_weights = None
        if method == "fossil" and fossils:
            fossil_weights = self._get_fossil_weights(fossils)

        item = self.create_item(base, ilvl, influences)

        for _ in range(iterations):
            for attempt in range(1, max_attempts + 1):
                if method == "fossil" and fossil_weights:
                    item.rarity = "rare"
                    self._roll_item(item, random.randint(4, 6), fossil_weights=fossil_weights)
                elif method == "alt":
                    item.rarity = "magic"
                    self._roll_item(item, random.randint(1, 2))
                else:
                    item.rarity = "rare"
                    self._roll_item(item, random.randint(4, 6))

                rolled_groups = {m.modgroup.lower() for m in item.all_mods}
                if match_mode == "all":
                    hit = target_set.issubset(rolled_groups)
                else:
                    hit = bool(target_set & rolled_groups)

                if hit:
                    hits += 1
                    attempts_on_hit.append(attempt)
                    break

        # Calculate cost per attempt
        prices = None
        with contextlib.suppress(Exception):
            prices = self.data.get_prices()

        if method == "fossil" and fossils:
            cost_per = self.data.get_craft_cost("fossil", prices=prices, fossils=fossils)
        elif method == "chaos":
            cost_per = 1.0
        elif method == "alt":
            cost_per = self.data.get_craft_cost("alt", prices=prices)
        else:
            cost_per = 1.0

        avg_attempts = (
            sum(attempts_on_hit) / len(attempts_on_hit) if attempts_on_hit else float("inf")
        )
        hit_rate = hits / iterations if iterations > 0 else 0

        # Percentiles
        percentiles = {}
        if attempts_on_hit:
            sorted_attempts = sorted(attempts_on_hit)
            for label, pct in [("p50", 0.5), ("p75", 0.75), ("p90", 0.9), ("p99", 0.99)]:
                idx = min(int(len(sorted_attempts) * pct), len(sorted_attempts) - 1)
                percentiles[label] = sorted_attempts[idx]

        return SimResult(
            method=method,
            iterations=iterations,
            hits=hits,
            hit_rate=hit_rate,
            avg_attempts=avg_attempts,
            avg_cost_chaos=avg_attempts * cost_per,
            cost_per_attempt=cost_per,
            percentiles=percentiles,
        )

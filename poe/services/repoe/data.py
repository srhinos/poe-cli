from __future__ import annotations

import copy
import json
import typing
from pathlib import Path

from poe.exceptions import SimDataError
from poe.services.repoe.constants import (
    CURRENCY_PATH_NAMES,
    ESSENCE_TIER_PREFIXES,
    INFLUENCE_TAG_MAP,
    MAX_RESONATOR_SOCKETS,
    RESONATOR_BY_SOCKETS,
)


class RepoEData:
    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or (
            Path(__file__).resolve().parent.parent.parent / "data" / "repoe"
        )
        self._cache: dict[str, dict | list] = {}

    def snapshot(self) -> RepoEData:
        clone = copy.copy(self)
        object.__setattr__(clone, "_cache", copy.deepcopy(self._cache))
        return clone

    def _load(self, name: str) -> dict | list:
        if name not in self._cache:
            path = self._data_dir / f"{name}.json"
            self._cache[name] = json.loads(path.read_text(encoding="utf-8"))
        return self._cache[name]

    def _find_base_item(self, name: str, base_items: dict) -> dict | None:
        item = base_items.get(name)
        if item is not None:
            return item
        for bname, bitem in base_items.items():
            if bname.casefold() == name.casefold():
                return bitem
        return None

    def get_base_item(self, name: str) -> dict | None:
        base_items = self._load("base_items")
        return self._find_base_item(name, base_items)

    def search_base_items(self, query: str) -> list[dict]:
        base_items = self._load("base_items")
        q = query.casefold()
        return [
            {**bitem, "name": bname} for bname, bitem in base_items.items() if q in bname.casefold()
        ]

    def get_mod_pool(
        self,
        base_name: str,
        ilvl: int = 100,
        influences: list[str] | None = None,
        affix_type: str | None = None,
    ) -> list[dict]:
        base_items = self._load("base_items")
        bitem = self._find_base_item(base_name, base_items)
        if not bitem:
            return []

        mods = self._load("mods")
        mod_pool = self._load("mod_pool")

        base_id = bitem["id"]
        mod_ids = mod_pool.get(base_id, [])
        allowed_influences: set[str | None] = {None}
        inf_tags: set[str] = set()
        inv_influence_map = {v: k for k, v in INFLUENCE_TAG_MAP.items()}
        for inf in influences or []:
            display = INFLUENCE_TAG_MAP.get(inf.casefold(), inf.title())
            allowed_influences.add(display)
            codename = inv_influence_map.get(inf, inf.casefold())
            for tag in bitem["tags"]:
                inf_tags.add(f"{tag}_{codename}")

        results = []
        for mid in mod_ids:
            mod = mods.get(mid)
            if not mod:
                continue
            if mod["influence"] not in allowed_influences:
                continue
            affix = mod["affix"]
            if affix_type and affix != affix_type:
                continue
            if mod["required_level"] > ilvl:
                continue

            best_weight = self._best_weight_for_base(mod, bitem, inf_tags or None)
            if best_weight <= 0:
                continue

            group_mods = self._get_group_tiers_from(mod["group"], base_id, ilvl, mod_pool, mods)

            results.append(
                {
                    "mod_id": mid,
                    "name": mod["name"],
                    "affix": affix,
                    "group": mod["group"],
                    "weight": best_weight,
                    "tier_count": len(group_mods),
                    "best_tier": {
                        "ilvl": mod["required_level"],
                        "values": [[s["min"], s["max"]] for s in mod["stats"]],
                        "weight": best_weight,
                    },
                    "implicit_tags": mod["implicit_tags"],
                    "influence": mod["influence"],
                }
            )

        results.sort(key=lambda x: x["weight"], reverse=True)
        return results

    @staticmethod
    def _best_weight_for_base(mod: dict, bitem: dict, extra_tags: set[str] | None = None) -> int:
        base_tags = set(bitem["tags"])
        if extra_tags:
            base_tags |= extra_tags
        for sw in mod["spawn_weights"]:
            if sw["tag"] in base_tags:
                return sw["weight"]
        return 0

    @staticmethod
    def _get_group_tiers_from(
        group: str, base_id: str, ilvl: int, mod_pool: dict, mods: dict
    ) -> list[str]:
        mod_ids = mod_pool.get(base_id, [])
        return [
            mid
            for mid in mod_ids
            if mods.get(mid, {}).get("group") == group and mods[mid]["required_level"] <= ilvl
        ]

    def get_mod_tiers(self, mod_id: str, base_name: str, ilvl: int = 100) -> list[dict]:
        base_items = self._load("base_items")
        bitem = self._find_base_item(base_name, base_items)
        if not bitem:
            return []

        mods = self._load("mods")
        mod = mods.get(mod_id)
        if not mod:
            return []

        mod_pool = self._load("mod_pool")
        base_id = bitem["id"]
        group = mod["group"]
        pool_ids = mod_pool.get(base_id, [])

        tier_mods = [(mid, m) for mid in pool_ids if (m := mods.get(mid)) and m["group"] == group]
        tier_mods.sort(key=lambda x: x[1]["required_level"], reverse=True)

        return [
            {
                "tier": i + 1,
                "ilvl": m["required_level"],
                "weight": self._best_weight_for_base(m, bitem),
                "values": [[s["min"], s["max"]] for s in m["stats"]],
                "available": m["required_level"] <= ilvl,
            }
            for i, (_mid, m) in enumerate(tier_mods)
        ]

    def get_fossils(self, filter_tag: str | None = None) -> list[dict]:
        fossils = self._load("fossils")
        results = []
        for name, fossil in fossils.items():
            if filter_tag:
                ft = filter_tag.casefold()
                all_tags = [
                    t.casefold()
                    for t in [
                        *fossil["positive_weights"],
                        *fossil["negative_weights"],
                        *fossil["blocked_tags"],
                    ]
                ]
                if not any(ft in t for t in all_tags):
                    continue
            results.append(
                {
                    "name": name,
                    "positive_weights": fossil["positive_weights"],
                    "negative_weights": fossil["negative_weights"],
                    "blocked": fossil["blocked_tags"],
                }
            )
        return results

    def get_essences(self, base_name: str | None = None) -> list[dict]:
        essences = self._load("essences")
        bitem = None
        item_class = None
        mods_data = None
        if base_name:
            base_items = self._load("base_items")
            bitem = self._find_base_item(base_name, base_items)
            if not bitem:
                raise SimDataError(f"Base item {base_name!r} not found")
            item_class = bitem["item_class"]
            mods_data = self._load("mods")

        results = []
        for name, ess in essences.items():
            tier_name, tier_num = self._extract_essence_tier(name)
            if base_name and bitem and item_class:
                mod_id = ess["mods"].get(item_class)
                if not mod_id:
                    continue
                mod = mods_data.get(mod_id) if mods_data else None
                mod_text = mod["name"] if mod else mod_id
                results.append(
                    {
                        "name": name,
                        "mods": [{"slot": item_class, "mod": mod_text}],
                        "tier": tier_name,
                        "tier_num": tier_num,
                    }
                )
            else:
                mods_list = [{"slot": ic, "mod": mid} for ic, mid in list(ess["mods"].items())[:5]]
                results.append(
                    {
                        "name": name,
                        "mods": mods_list,
                        "total_slots": len(ess["mods"]),
                        "tier": tier_name,
                        "tier_num": tier_num,
                    }
                )
        return results

    @staticmethod
    def _extract_essence_tier(name: str) -> tuple[str, int]:
        name_lower = name.casefold()
        for prefix, tier_num in ESSENCE_TIER_PREFIXES.items():
            if name_lower.startswith(prefix):
                return prefix.title(), tier_num
        return "", 0

    def get_bench_crafts(self, base_name: str) -> list[dict]:
        base_items = self._load("base_items")
        bitem = self._find_base_item(base_name, base_items)
        if not bitem:
            return []

        mods = self._load("mods")
        bench_crafts = self._load("bench_crafts")
        item_class = bitem["item_class"]

        results = []
        for craft in bench_crafts:
            if item_class not in craft["item_classes"]:
                continue
            mod = mods.get(craft["mod_id"])
            if not mod:
                continue
            affix = mod["affix"]
            if affix not in ("prefix", "suffix"):
                continue
            cost_parts = [
                f"{count}x {CURRENCY_PATH_NAMES.get(cname, cname)}"
                for cname, count in craft["cost"].items()
            ]
            values = [[s["min"], s["max"]] for s in mod["stats"]]
            results.append(
                {
                    "mod_id": craft["mod_id"],
                    "name": mod["name"],
                    "affix": affix,
                    "group": mod["group"],
                    "cost": ", ".join(cost_parts),
                    "cost_raw": craft["cost"],
                    "values": values,
                }
            )
        return results

    def get_prices(self, league: str = "current") -> dict:
        return {
            "league": league,
            "currency": {},
            "fossils": {},
            "essences": {},
            "resonators": {},
            "beasts": {},
            "other": {},
        }

    def get_craft_cost(self, method: str, prices: dict | None = None, **kwargs: object) -> float:
        if prices is None:
            prices = self.get_prices()
        currency = prices.get("currency", {})
        cost_map = {
            "chaos": 1.0,
            "alt": float(currency.get("Orb of Alteration", 0.05)),
            "regal": float(currency.get("Regal Orb", 1)),
            "exalt": float(currency.get("Exalted Orb", 10)),
            "annul": float(currency.get("Orb of Annulment", 5)),
            "divine": float(currency.get("Divine Orb", 150)),
            "scour": float(currency.get("Orb of Scouring", 0.5)),
        }
        if method in cost_map:
            return cost_map[method]
        if method == "fossil":
            fossil_names = typing.cast("list[str]", kwargs.get("fossils", []))
            fossil_prices = prices.get("fossils", {})
            total = 0.0
            for fname in fossil_names:
                price = fossil_prices.get(fname)
                if price is None:
                    short = fname.replace(" Fossil", "")
                    price = fossil_prices.get(short, 5)
                total += float(price)
            res_prices = prices.get("resonators", {})
            res_name, res_default = RESONATOR_BY_SOCKETS.get(
                min(len(fossil_names), MAX_RESONATOR_SOCKETS),
                ("Prime Alchemical Resonator", 10),
            )
            total += float(res_prices.get(res_name, res_default))
            return total
        if method == "essence":
            essence_name = typing.cast("str", kwargs.get("essence", ""))
            essence_prices = prices.get("essences", {})
            return float(essence_prices.get(essence_name, 5))
        return 1.0

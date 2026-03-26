"""Craft of Exile data layer — fetch, cache, and query CoE game data."""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime
from pathlib import Path

import httpx

# ── CoE endpoint definitions ────────────────────────────────────────────────

_BASE_URL = "https://www.craftofexile.com/"

_ENDPOINTS: dict[str, dict] = {
    "data": {
        "path": "json/data/main/poec_data.json",
        "prefix": "poecd=",
        "ttl": 14 * 24 * 3600,  # 2 weeks
    },
    "common": {
        "path": "json/data/poec_common.json",
        "prefix": "poecc=",
        "ttl": 14 * 24 * 3600,
    },
    "exdata": {
        "path": "json/data/exdata/poec_exdata.json",
        "prefix": "poeexd=",
        "ttl": 14 * 24 * 3600,
    },
    "prices": {
        "path": "json/data/prices/poec_prices.json",
        "prefix": "poecp=",
        "ttl": 4 * 3600,  # 4 hours base, jitter added
    },
    "affinities": {
        "path": "json/data/affinities/poec_affinities.json",
        "prefix": "poeaf=",
        "ttl": 4 * 3600,
    },
}

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.craftofexile.com/",
    "Accept": "*/*",
}


def _cache_dir() -> Path:
    d = Path.home() / ".cache" / "pob-mcp" / "coe"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _meta_path(cache_file: Path) -> Path:
    return cache_file.with_suffix(".meta")


def _strip_js_wrapper(text: str, prefix: str) -> str:
    """Strip JS variable assignment prefix and trailing semicolon."""
    if text.startswith(prefix):
        text = text[len(prefix) :]
    elif "=" in text[:30]:
        text = text[text.index("=") + 1 :]
    text = text.rstrip()
    if text.endswith(";"):
        text = text[:-1]
    return text


# ── CraftData ────────────────────────────────────────────────────────────────


class CraftData:
    """Cached Craft of Exile data access."""

    def __init__(self) -> None:
        self._cache_dir = _cache_dir()
        self._data: dict[str, dict] = {}

    # ── data loading ──────────────────────────────────────────────────────

    def _cache_file(self, name: str) -> Path:
        return self._cache_dir / f"{name}.json"

    def _is_fresh(self, name: str) -> bool:
        meta = _meta_path(self._cache_file(name))
        if not meta.exists():
            return False
        try:
            info = json.loads(meta.read_text())
            fetched = datetime.fromisoformat(info["fetched_at"])
            ttl = _ENDPOINTS[name]["ttl"]
            # Add jitter for short-TTL files
            if ttl <= 4 * 3600:
                ttl += random.randint(0, 3600)
            age = (datetime.now(UTC) - fetched).total_seconds()
            return age < ttl
        except (KeyError, ValueError, json.JSONDecodeError):
            return False

    def _fetch_one(self, name: str, force: bool = False) -> dict:
        """Fetch or load from cache a single data file."""
        cache_file = self._cache_file(name)
        meta_file = _meta_path(cache_file)
        ep = _ENDPOINTS[name]

        if not force and cache_file.exists() and self._is_fresh(name):
            return json.loads(cache_file.read_text(encoding="utf-8"))

        # Fetch from CoE
        url = _BASE_URL + ep["path"]
        etag = None
        last_modified = None
        if meta_file.exists():
            try:
                info = json.loads(meta_file.read_text())
                etag = info.get("etag")
                last_modified = info.get("last_modified")
            except (json.JSONDecodeError, KeyError):
                pass

        headers = dict(_HEADERS)
        if etag and not force:
            headers["If-None-Match"] = etag
        if last_modified and not force:
            headers["If-Modified-Since"] = last_modified

        resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=60)

        if resp.status_code == 304 and cache_file.exists():
            # Not modified — update timestamp
            meta = json.loads(meta_file.read_text())
            meta["fetched_at"] = datetime.now(UTC).isoformat()
            meta_file.write_text(json.dumps(meta))
            return json.loads(cache_file.read_text(encoding="utf-8"))

        resp.raise_for_status()
        raw = resp.text

        # Validate we got JSON, not HTML
        if raw.lstrip().startswith("<!DOCTYPE") or raw.lstrip().startswith("<html"):
            raise RuntimeError(f"CoE returned HTML instead of JSON for {name}. Try again later.")

        body = _strip_js_wrapper(raw, ep["prefix"])
        data = json.loads(body)

        # Write cache
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        meta_info = {
            "fetched_at": datetime.now(UTC).isoformat(),
            "etag": resp.headers.get("etag"),
            "last_modified": resp.headers.get("last-modified"),
        }
        meta_file.write_text(json.dumps(meta_info))

        return data

    def ensure_data(self, force: bool = False) -> None:
        """Load all data files, fetching from CoE if stale."""
        for name in ("data", "common"):
            self._data[name] = self._fetch_one(name, force=force)

    def _ensure_loaded(self, name: str) -> dict:
        if name not in self._data:
            self._data[name] = self._fetch_one(name)
        return self._data[name]

    def _main(self) -> dict:
        return self._ensure_loaded("data")

    def _common(self) -> dict:
        return self._ensure_loaded("common")

    def _exdata(self) -> dict:
        return self._ensure_loaded("exdata")

    def _prices_raw(self) -> dict:
        return self._ensure_loaded("prices")

    # ── base items ────────────────────────────────────────────────────────

    def get_base_item(self, name: str) -> dict | None:
        """Look up a base item by name (e.g. 'Archdemon Crown')."""
        d = self._main()
        idx = d["bitems"]["name"].get(name)
        if idx is None:
            # Try case-insensitive
            for bname, bidx in d["bitems"]["name"].items():
                if bname.lower() == name.lower():
                    idx = bidx
                    break
        if idx is None:
            return None
        return d["bitems"]["seq"][int(idx)]

    def get_base_group(self, base_id: str) -> dict | None:
        """Get the base group (e.g. Helmets, Body Armours) for a base_id."""
        d = self._main()
        for b in d["bases"]["seq"]:
            if b["id_base"] == base_id:
                bg_id = b["id_bgroup"]
                for bg in d["bgroups"]["seq"]:
                    if bg["id_bgroup"] == bg_id:
                        return bg
        return None

    def get_base_info(self, base_id: str) -> dict | None:
        """Get base info entry by base_id."""
        d = self._main()
        for b in d["bases"]["seq"]:
            if b["id_base"] == base_id:
                return b
        return None

    def search_base_items(self, query: str) -> list[dict]:
        """Fuzzy search base items by name."""
        d = self._main()
        q = query.lower()
        results = []
        for bname, idx in d["bitems"]["name"].items():
            if q in bname.lower():
                results.append(d["bitems"]["seq"][int(idx)])
        return results

    # ── mod pools ─────────────────────────────────────────────────────────

    def _get_modifier(self, mod_id: str) -> dict | None:
        d = self._main()
        idx = d["modifiers"]["ind"].get(mod_id)
        if idx is None:
            return None
        return d["modifiers"]["seq"][int(idx)]

    def _get_influence_mgroup_ids(self, influences: list[str]) -> list[str]:
        """Map influence names to mgroup IDs."""
        d = self._main()
        name_map = {
            "shaper": "Shaper",
            "elder": "Elder",
            "crusader": "Crusader",
            "hunter": "Hunter",
            "redeemer": "Redeemer",
            "warlord": "Warlord",
        }
        ids = ["1"]  # Base mods always included
        for inf in influences:
            target = name_map.get(inf.lower(), inf)
            for mg in d["mgroups"]["seq"]:
                if mg["name_mgroup"].lower() == target.lower():
                    ids.append(mg["id_mgroup"])
                    break
        return ids

    def get_mod_pool(
        self,
        base_name: str,
        ilvl: int = 100,
        influences: list[str] | None = None,
        affix_type: str | None = None,
    ) -> list[dict]:
        """Get rollable mods for a base item at given ilvl.

        Returns list of dicts with modifier info + best available tier.
        affix_type: "prefix", "suffix", or None for both.
        """
        bitem = self.get_base_item(base_name)
        if not bitem:
            return []

        d = self._main()
        base_id = bitem["id_base"]
        mod_ids = d["basemods"].get(base_id, [])
        allowed_mgroups = self._get_influence_mgroup_ids(influences or [])

        results = []
        for mid in mod_ids:
            mod = self._get_modifier(mid)
            if not mod:
                continue

            # Filter by mod group (influence)
            if mod["id_mgroup"] not in allowed_mgroups:
                continue

            # Filter by affix type
            affix = mod["affix"]
            if affix_type:
                if affix_type == "prefix" and affix != "prefix":
                    continue
                if affix_type == "suffix" and affix != "suffix":
                    continue
            elif affix not in ("prefix", "suffix"):
                # Skip eldritch/other mod types unless specifically requested
                continue

            # Get best tier at this ilvl
            tiers = self._get_tiers_for_mod(mid, base_id, ilvl)
            if not tiers:
                continue

            best = tiers[0]  # Highest ilvl tier that fits
            weight = int(best["weighting"])
            if weight <= 0:
                continue

            # Parse mod tags
            mtypes = []
            raw_mtypes = mod.get("mtypes")
            if raw_mtypes:
                if isinstance(raw_mtypes, str):
                    mtypes = [t for t in raw_mtypes.split("|") if t]
                else:
                    mtypes = list(raw_mtypes)

            results.append(
                {
                    "mod_id": mid,
                    "name": mod["name_modifier"],
                    "affix": affix,
                    "modgroup": mod["modgroup"],
                    "weight": weight,
                    "tier_count": len(tiers),
                    "best_tier": {
                        "ilvl": int(best["ilvl"]),
                        "values": json.loads(best["nvalues"])
                        if isinstance(best["nvalues"], str)
                        else best["nvalues"],
                        "weight": weight,
                    },
                    "mtypes": mtypes,
                    "influence": self._mgroup_name(mod["id_mgroup"]),
                }
            )

        # Sort by weight descending
        results.sort(key=lambda x: x["weight"], reverse=True)
        return results

    def _mgroup_name(self, mgroup_id: str) -> str:
        if mgroup_id == "1":
            return "Base"
        d = self._main()
        for mg in d["mgroups"]["seq"]:
            if mg["id_mgroup"] == mgroup_id:
                return mg["name_mgroup"]
        return f"Unknown({mgroup_id})"

    def _get_tiers_for_mod(self, mod_id: str, base_id: str, ilvl: int) -> list[dict]:
        """Get available tiers for a mod on a base at a given ilvl, highest first."""
        d = self._main()
        if mod_id not in d["tiers"]:
            return []
        base_tiers = d["tiers"][mod_id].get(base_id)
        if not base_tiers:
            return []

        available = [t for t in base_tiers if int(t["ilvl"]) <= ilvl]
        # Sort by ilvl descending (best tier first)
        available.sort(key=lambda t: int(t["ilvl"]), reverse=True)
        return available

    def get_mod_tiers(self, mod_id: str, base_name: str, ilvl: int = 100) -> list[dict]:
        """Get all tiers for a specific mod on a base item."""
        bitem = self.get_base_item(base_name)
        if not bitem:
            return []
        base_id = bitem["id_base"]

        d = self._main()
        if mod_id not in d["tiers"]:
            return []
        base_tiers = d["tiers"][mod_id].get(base_id)
        if not base_tiers:
            return []

        result = []
        for i, t in enumerate(sorted(base_tiers, key=lambda x: int(x["ilvl"]), reverse=True)):
            tier_num = i + 1
            values = json.loads(t["nvalues"]) if isinstance(t["nvalues"], str) else t["nvalues"]
            result.append(
                {
                    "tier": tier_num,
                    "ilvl": int(t["ilvl"]),
                    "weight": int(t["weighting"]),
                    "values": values,
                    "available": int(t["ilvl"]) <= ilvl,
                }
            )
        return result

    # ── fossils ───────────────────────────────────────────────────────────

    def get_fossils(self, filter_tag: str | None = None) -> list[dict]:
        """Get fossil list, optionally filtered by tag name."""
        d = self._main()
        mtypes_by_id = {m["id_mtype"]: m["name_mtype"] for m in d["mtypes"]["seq"]}

        results = []
        for f in d["fossils"]["seq"]:
            mod_data = (
                json.loads(f["mod_data"])
                if isinstance(f["mod_data"], str)
                else (f["mod_data"] or {})
            )

            # Resolve more/less/block lists to tag names
            more = self._resolve_mtype_list(f.get("more_list"), mtypes_by_id)
            less = self._resolve_mtype_list(f.get("less_list"), mtypes_by_id)
            blocked = self._resolve_mtype_list(f.get("block_list"), mtypes_by_id)

            if filter_tag:
                ft = filter_tag.lower()
                all_tags = [t.lower() for t in more + less + blocked]
                if not any(ft in t for t in all_tags):
                    continue

            results.append(
                {
                    "id": f["id_fossil"],
                    "name": f["name_fossil"],
                    "more_likely": more,
                    "less_likely": less,
                    "blocked": blocked,
                    "mod_weights": mod_data,
                }
            )
        return results

    def _resolve_mtype_list(self, pipe_str: str | None, mtypes: dict) -> list[str]:
        if not pipe_str:
            return []
        ids = [x for x in pipe_str.split("|") if x]
        return [mtypes.get(i, f"tag_{i}") for i in ids]

    # ── essences ──────────────────────────────────────────────────────────

    def get_essences(self, base_name: str | None = None) -> list[dict]:
        """Get essences, optionally filtered to those relevant for a base item."""
        d = self._main()
        bitem = None
        base_id = None
        if base_name:
            bitem = self.get_base_item(base_name)
            if bitem:
                base_id = bitem["id_base"]
                for b in d["bases"]["seq"]:
                    if b["id_base"] == base_id:
                        break

        results = []
        for e in d["essences"]["seq"]:
            tooltip = (
                json.loads(e["tooltip"]) if isinstance(e["tooltip"], str) else (e["tooltip"] or [])
            )

            if base_name and bitem:
                # Filter: find if this essence has an entry matching the base group
                relevant = []
                for entry in tooltip:
                    # entry["bid"] contains base IDs this applies to
                    bids = entry.get("bid", [])
                    if base_id and int(base_id) in [int(b) for b in bids]:
                        relevant.append({"slot": entry["lbl"], "mod": entry["val"]})
                if not relevant:
                    continue
                results.append(
                    {
                        "id": e["id_essence"],
                        "name": f"Essence of {e['name_essence']}",
                        "mods": relevant,
                    }
                )
            else:
                mods = [{"slot": entry["lbl"], "mod": entry["val"]} for entry in tooltip]
                results.append(
                    {
                        "id": e["id_essence"],
                        "name": f"Essence of {e['name_essence']}",
                        "mods": mods[:5],  # Truncate for overview
                        "total_slots": len(mods),
                    }
                )

        return results

    # ── bench crafts ──────────────────────────────────────────────────────

    def get_bench_crafts(self, base_name: str) -> list[dict]:
        """Get available bench crafts for a base item."""
        bitem = self.get_base_item(base_name)
        if not bitem:
            return []

        d = self._main()
        common = self._common()
        base_id = bitem["id_base"]

        # Find bench-craftable mods in the mod pool
        mod_ids = d["basemods"].get(base_id, [])
        results = []

        for mid in mod_ids:
            mod = self._get_modifier(mid)
            if not mod:
                continue

            # Check if this mod has bench costs
            cost_key = f"{mid}b{base_id}"
            costs = common["benchcosts"].get(cost_key)
            if not costs:
                # Also try with base group
                base_info = self.get_base_info(base_id)
                if base_info:
                    # Try various base group keys
                    for b in d["bases"]["seq"]:
                        if b["id_base"] == base_id:
                            cost_key2 = f"{mid}b{b['id_bgroup']}"
                            costs = common["benchcosts"].get(cost_key2)
                            if costs:
                                break
            if not costs:
                continue

            # Parse costs into readable format
            cost_str = self._format_bench_cost(costs)
            affix = mod["affix"]
            if affix not in ("prefix", "suffix"):
                continue

            tiers = self._get_tiers_for_mod(mid, base_id, 100)
            values = None
            if tiers:
                values = (
                    json.loads(tiers[0]["nvalues"])
                    if isinstance(tiers[0]["nvalues"], str)
                    else tiers[0]["nvalues"]
                )

            results.append(
                {
                    "mod_id": mid,
                    "name": mod["name_modifier"],
                    "affix": affix,
                    "modgroup": mod["modgroup"],
                    "cost": cost_str,
                    "cost_raw": costs,
                    "values": values,
                }
            )

        return results

    def _format_bench_cost(self, costs: list[dict]) -> str:
        """Format bench craft costs to human-readable string."""
        # Currency IDs: 1=Orb of Transmutation, 2=Orb of Alteration, 3=Chaos Orb,
        # 4=Exalted Orb, 5=Orb of Scouring, 6=Vaal Orb, 7=Divine Orb
        currency_names = {
            "1": "Transmutation",
            "2": "Alteration",
            "3": "Chaos",
            "4": "Exalted",
            "5": "Scouring",
            "6": "Vaal",
            "7": "Divine",
        }
        parts = []
        for cost_entry in costs:
            for cid, count in cost_entry.items():
                name = currency_names.get(cid, f"Currency({cid})")
                parts.append(f"{count}x {name}")
        return ", ".join(parts)

    # ── prices ────────────────────────────────────────────────────────────

    def get_prices(self, league: str = "current") -> dict:
        """Get current prices from poe.ninja via CoE cache."""
        prices = self._prices_raw()
        leagues = prices.get("index", [])

        if league == "current" and leagues:
            league_id = leagues[0]["id"]
        else:
            league_id = None
            for lg in leagues:
                if lg["name"].lower() == league.lower() or lg["id"] == league:
                    league_id = lg["id"]
                    break
            if not league_id and leagues:
                league_id = leagues[0]["id"]

        if not league_id:
            return {"error": "No league data available"}

        # Price data is keyed by league name, not ID
        league_name = next((lg["name"] for lg in leagues if lg["id"] == league_id), league_id)
        league_data = prices.get("data", {}).get(league_name, {})
        if not league_data:
            # Fallback: try by ID
            league_data = prices.get("data", {}).get(league_id, {})
        return {
            "league": league_name,
            "currency": league_data.get("currency", {}),
            "fossils": league_data.get("fossils", {}),
            "essences": league_data.get("essences", {}),
            "resonators": league_data.get("resonators", {}),
            "beasts": league_data.get("beasts", {}),
            "other": league_data.get("other", {}),
        }

    def get_craft_cost(self, method: str, prices: dict | None = None, **kwargs) -> float:
        """Estimate cost in chaos for a single crafting action."""
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
            fossil_names = kwargs.get("fossils", [])
            fossil_prices = prices.get("fossils", {})
            total = 0.0
            for fname in fossil_names:
                # Try exact match, then without " Fossil" suffix
                price = fossil_prices.get(fname)
                if price is None:
                    short = fname.replace(" Fossil", "")
                    price = fossil_prices.get(short, 5)
                total += float(price)
            # Add resonator cost
            n = len(fossil_names)
            res_prices = prices.get("resonators", {})
            if n == 1:
                total += float(res_prices.get("Primitive Alchemical Resonator", 1))
            elif n == 2:
                total += float(res_prices.get("Potent Alchemical Resonator", 2))
            elif n == 3:
                total += float(res_prices.get("Powerful Alchemical Resonator", 5))
            elif n >= 4:
                total += float(res_prices.get("Prime Alchemical Resonator", 10))
            return total

        if method == "essence":
            essence_name = kwargs.get("essence", "")
            essence_prices = prices.get("essences", {})
            return float(essence_prices.get(essence_name, 5))

        return 1.0  # fallback

    # ── cache management ──────────────────────────────────────────────────

    def update_data(self) -> dict:
        """Force refresh all data files. Returns status dict."""
        results = {}
        for name in _ENDPOINTS:
            try:
                self._data[name] = self._fetch_one(name, force=True)
                cf = self._cache_file(name)
                results[name] = {
                    "status": "ok",
                    "size": cf.stat().st_size if cf.exists() else 0,
                }
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        return results

    def cache_status(self) -> dict:
        """Get cache status for all data files."""
        status = {}
        for name in _ENDPOINTS:
            cf = self._cache_file(name)
            mf = _meta_path(cf)
            entry: dict = {"cached": cf.exists()}
            if mf.exists():
                try:
                    meta = json.loads(mf.read_text())
                    entry["fetched_at"] = meta.get("fetched_at")
                    entry["fresh"] = self._is_fresh(name)
                except (json.JSONDecodeError, KeyError):
                    entry["meta_corrupt"] = True
            if cf.exists():
                entry["size_kb"] = round(cf.stat().st_size / 1024, 1)
            status[name] = entry
        return status

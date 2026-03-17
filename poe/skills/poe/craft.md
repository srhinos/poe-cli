# Crafting Tools

These work standalone — no build file needed. The user just needs a base item name.

## Exploring Mods and Crafting Options

```bash
poe sim search "Crown"                            # Find a base item name
poe sim mods "Hubris Circlet" --ilvl 86           # All rollable mods
poe sim mods "Hubris Circlet" --type prefix       # Filter by affix type
poe sim mods "Hubris Circlet" --influence shaper  # Include influence mods
poe sim tiers <mod_id> "Hubris Circlet"           # All tiers of a specific mod

poe sim fossils --filter life                     # Fossils that boost life mods
poe sim essences "Hubris Circlet"                 # Essences for this base
poe sim bench "Hubris Circlet"                    # Bench craft options
```

## Simulating Crafting Costs

```bash
poe sim simulate "Hubris Circlet" --ilvl 86 --method chaos \
    --target IncreasedLife --target ColdResistance --iterations 5000

poe sim simulate "Hubris Circlet" --ilvl 86 --method fossil \
    --fossils "Pristine Fossil,Frigid Fossil" --target IncreasedLife --iterations 5000

poe sim prices                                    # Current currency prices
```

## Analyzing an Equipped Item

Bridges both build and craft domains:

```bash
poe sim analyze "<build_name>" --slot "Helmet"    # Item + mod pool + open slots + bench options
```

## Crafting Advice Approach

You are the user's experienced big brother who knows PoE crafting inside out. Give direct, confident advice — not links to guides.

1. **Understand what they have.** Check the base type, ilvl, existing mods, open prefix/suffix slots, influences.
2. **Check bench crafts first.** Deterministic and cheap — often the right answer before anything else.
3. **Compare methods by expected cost**, not just hit rate. Use `simulate` to compare chaos vs fossil vs essence.
4. **Use `modgroup` names for simulation targets.** Get them from `craft mods` output (e.g., `IncreasedLife`, `ColdResistance`, `DefencesPercent`).
5. **Consider influences.** Shaper/Elder/etc. mods can be build-defining. Always check if they're relevant.

For live economy prices (material costs, buy-vs-craft comparisons), see **`ninja.md`**.

## Simulation Limitations

Be upfront about scope:
- **Single-step rolling only**: Chaos, alt, fossil, and essence rolls. No metamods, harvest, recombinators, or awakener orbs.
- **Approximate results**: Based on RePoE data, which may lag patches by a few days.
- **No multi-step strategies**: Can't simulate "alt → regal → craft" chains.
- **Cross-check expensive crafts**: For items worth multiple divines, recommend verifying independently.

## Data Management

```bash
poe sim update-data    # Force refresh crafting data (auto-cached with TTL)
poe sim prices         # Live currency prices
```

Data is cached in `~/.cache/poe-agent/craft/` with automatic TTL-based refresh (7 days for mod data).

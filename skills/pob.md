---
name: pob
description: Use when the user asks about their Path of Exile build, Path of Building, build analysis, passive tree, items, gems, DPS, defenses, resistances, crafting advice, item upgrades, or anything related to PoE character optimization.
---

# Path of Building CLI Toolkit

You have access to the `pob` CLI tool for analyzing Path of Building builds. Use Bash to run commands. All commands output JSON by default. Add `--human` for readable output.

## Approach: Overview First

PoB builds are complex — they can contain multiple tree specs, item sets, skill sets, disabled gems, and build notes. **Always start with a high-level overview before drilling into details.**

### Step 1: Get the lay of the land
```bash
uv run pob builds list                          # What builds are available?
uv run pob builds analyze "<name>"              # High-level overview (specs, sets, stats, notes)
uv run pob builds notes "<name>"                # Build notes (often contain guide info, gearing plans)
```

The `analyze` output tells you:
- How many tree specs, item sets, and skill sets exist (and which are active)
- Whether this is a single build, a leveling guide, or a multi-phase plan
- The build's current stats snapshot

### Step 2: Ask the user what they need
Don't assume. A build with 8 tree specs named "Leveling 1" through "Leveling 7" is a leveling guide — the user might want help at any stage. A build imported from their character might have multiple snapshots at different levels. Ask which phase or loadout they're working with.

### Step 3: Drill into the relevant loadout
```bash
uv run pob tree specs "<name>"                  # List all tree specs with titles and node counts
uv run pob tree get "<name>" --spec 3           # Get a specific tree spec
uv run pob tree get "<name>"                    # Get the active spec (default)

uv run pob items sets "<name>"                  # List all item sets
uv run pob items list "<name>" --item-set 3     # Items from a specific set
uv run pob items list "<name>"                  # Active item set (default)

uv run pob gems sets "<name>"                   # List all skill sets
uv run pob gems list "<name>" --skill-set 2     # Gems from a specific set
uv run pob gems list "<name>"                   # Active skill set (default)
```

### Step 4: Compare, validate, dig deeper
```bash
uv run pob builds stats "<name>" --category off  # Offensive stats
uv run pob builds stats "<name>" --category def  # Defensive stats
uv run pob builds compare "<build1>" "<build2>"  # Side-by-side stat diff
uv run pob tree compare "<build1>" "<build2>"     # Tree node diff
uv run pob builds validate "<name>"               # Check for common issues
uv run pob config get "<name>"                    # Build configuration (charges, conditions, enemy)
```

### Step 5: Create and modify builds
```bash
# Create a new build
uv run pob builds create "<name>" --class-name Witch --ascendancy Necromancer --level 90
uv run pob builds create "<name>" --file /path/to/output.xml   # Explicit output path

# Delete a build (requires --confirm)
uv run pob builds delete "<name>" --confirm

# Add/remove items
uv run pob items add "<name>" --slot Helmet --rarity RARE --item-name "Doom Crown" \
    --base "Hubris Circlet" --energy-shield 200 --quality 20 --influence Shaper \
    --implicit "+(50-70) to maximum Life" --explicit "+90 to maximum Life" \
    --crafted-mod "+10% to all Elemental Resistances"
uv run pob items remove "<name>" --slot Helmet       # Remove by slot
uv run pob items remove "<name>" --id 3              # Remove by item ID

# Add/remove skill groups
uv run pob gems add "<name>" --slot "Body Armour" --gem Fireball --gem "Spell Echo Support" \
    --level 20 --quality 20 --include-full-dps
uv run pob gems remove "<name>" --index 0            # Remove skill group by 0-based index

# Modify passive tree
uv run pob tree set "<name>" --nodes 100,200,300     # Replace all nodes
uv run pob tree set "<name>" --add-nodes 500,600     # Add nodes incrementally
uv run pob tree set "<name>" --remove-nodes 100,200  # Remove specific nodes
uv run pob tree set "<name>" --mastery 53188:64875 --mastery 53738:29161
uv run pob tree set "<name>" --class-id 5 --ascend-class-id 2 --version 3_25
uv run pob tree set "<name>" --spec 2 --nodes 100,200  # Target a specific spec (1-based)

# Set configuration values
uv run pob config set "<name>" --boolean useFrenzyCharges=true --number enemyPhysicalHitDamage=5000
uv run pob config set "<name>" --string customMod="some value"
uv run pob config set "<name>" --remove useFrenzyCharges   # Remove a config key

# Set build notes
uv run pob builds notes "<name>" --set "Updated notes text"
```

All write commands accept `--file <path>` to specify an explicit file path instead of resolving by name from the builds directory.

### Other commands
```bash
uv run pob builds decode <build_code>            # Decode a PoB sharing code to XML
uv run pob builds export "<name>" <destination>  # Copy build file

uv run pob engine load "<name>"                  # Load into PoB's Lua engine for live calculated stats
uv run pob engine info                           # PoB version, Lua runtime info
```

## Understanding PoB Build Structure

### Multiple Specs / Sets
PoB builds frequently contain multiple loadouts. Common patterns:
- **Leveling guides**: tree specs named "Leveling 1-7", skill sets progressing from early gems to endgame links, item sets from campaign gear to endgame uniques
- **Imported characters**: a tree spec snapshot at each level when the character was imported
- **Gear progression**: item sets for budget → midrange → endgame gear
- **Skill variants**: different skill sets for mapping vs bossing

### Disabled Gems
Gems with `enabled: false` in a skill group are intentional — they represent:
- Gem swaps (e.g., swap in Concentrated Effect for bosses, swap out for mapping)
- Future upgrades the build creator plans to use later
- Alternate options the user hasn't chosen yet

### Config Section
The config controls assumptions that dramatically affect stats:
- `usePowerCharges`, `useFrenzyCharges`, `useEnduranceCharges` — are charges active?
- `conditionEnemyShocked`, `conditionEnemyChilled` — enemy ailment conditions
- `customMods` — manually added modifiers (**check these** — they can inflate stats)
- `ailmentMode` — how ailments are calculated

**Always compare configs** when comparing builds. A build showing 10M DPS with frenzy charges + custom mods enabled is not comparable to one without them.

### Build Notes
Notes often contain critical context: gearing strategies, gem swap instructions, crafting guides, playstyle tips, FAQ. Always read them.

## Interpreting Stats

### Offensive
- `TotalDPS` / `CombinedDPS` — single-skill DPS
- `FullDPS` — total across all skills marked "include in Full DPS" (often 0 if not configured)
- `AverageHit` — average damage per hit
- `CritChance` / `CritMultiplier` — critical strike stats
- `Speed` — attacks/casts per second
- `HitChance` — accuracy (100% for spells)

### Defensive
- `Life`, `EnergyShield` — HP pools
- `TotalEHP` — effective HP accounting for mitigation
- `FireResist`, `ColdResist`, `LightningResist` — elemental resists (cap 75%)
- `ChaosResist` — chaos res (default -60%)
- `FireResistOverCap` etc. — buffer above cap for curses/map mods
- `Armour`, `Evasion`, `PhysicalDamageReduction`
- `EffectiveBlockChance`, `EffectiveSpellBlockChance`
- `EffectiveSpellSuppressionChance`
- `PhysicalMaximumHitTaken` etc. — one-shot thresholds
- `Spec:LifeInc` — % increased life from passive tree (key survivability metric)

## PoE Mechanics Reference

### Damage
- **"More" multipliers** are multiplicative with each other (huge value). **"Increased"** is additive (diminishing returns).
- Each support gem in a link typically provides a "more" multiplier — a 6th link is often 30-40% more total DPS.
- Gem quality provides smaller bonuses. Level 20 + quality 20 is standard endgame. GCP recipe: level 20 gem + GCP = level 1 / quality 20.
- Crit builds need 60%+ crit chance to justify the investment. Below ~50%, scaling hit damage or DoT is usually better.

### Defenses
- **Elemental resistances**: must be capped at 75%. Overcap by 30-50% to handle curses and map mods.
- **Chaos resistance**: starts at -60%. Getting to 0% is a big survivability gain. Positive is luxury.
- **Life pool**: 3000 is bare minimum for mapping. 4000+ is comfortable. 5000+ is solid. Under 3000 means one-shots.
- `Spec:LifeInc` under 100% on the passive tree is a red flag — the tree needs more life nodes.
- **Spell suppression**: 100% or don't invest at all. Partial suppression is wasted points.
- **Block**: attack block without spell block leaves a hole. Check both.
- **Defensive layers**: good builds stack 2-3 layers (evasion + block, armour + endurance charges, ES + block, etc.)

### Passive Tree
- ~120 points at level 100 (plus quest rewards).
- Keystones define build identity (e.g., CI, Acrobatics, Resolute Technique).
- Notables are high-value nodes. Small nodes are mostly pathing.
- Jewel sockets hold regular, abyss, cluster, or timeless jewels.

### Gem Links
- 6-link is max sockets: 1 active skill + 5 support gems.
- Support gems must match skill tags (attack supports don't work with spells).
- Some active gems go in the helmet/gloves/boots with fewer links for utility setups.

## Crafting Advice Workflow

You are the user's experienced big brother who knows PoE crafting inside out. Give direct, confident advice — not links to guides or external tools. You have all the data.

### Approach: Understand → Analyze → Advise

**Step 1: Understand the item**
```bash
uv run pob items list "<name>"                    # See all equipped items with full mod details
```
Look at the target item's base type, influences, rarity, open prefix/suffix slots, existing mods (especially crafted and custom mods).

**Step 2: Analyze with CoE data**
```bash
uv run pob craft analyze "<name>" --slot "Helmet"  # Full analysis: item + mod pool + tiers + bench options
```
This shows you:
- The item's current mods and what slots are open
- How many rollable prefixes/suffixes exist at the item's ilvl
- Top available mods for open slots
- Bench craft options with costs

**Step 3: Explore options**
```bash
# What mods can roll?
uv run pob craft mods "<base>" --ilvl 86 --influence shaper --type prefix
uv run pob craft mods "<base>" --ilvl 86 --type suffix

# What fossils help?
uv run pob craft fossils --filter cold
uv run pob craft fossils --filter life

# What essences work?
uv run pob craft essences "<base>"

# Bench crafts available?
uv run pob craft bench "<base>"

# Search for a base item name
uv run pob craft search "Crown"

# All tiers of a specific mod
uv run pob craft tiers <mod_id> "<base>" --ilvl 86
```

**Step 4: Estimate costs**
```bash
# How many attempts to hit target mods?
uv run pob craft simulate "<base>" --ilvl 86 --method chaos --target IncreasedLife --target ColdResistance --iterations 5000

# Fossil crafting cost comparison
uv run pob craft simulate "<base>" --ilvl 86 --method fossil --fossils "Frigid,Bound" --target ColdResistance --target IncreasedLife --iterations 5000

# Current prices
uv run pob craft prices
```

**Step 5: Synthesize into direct advice**
Combine all the data into clear recommendations:
- "Your helmet has 3 open prefixes. The best use is to bench craft +Life/ES% for 2 Chaos, then use Aisling to upgrade."
- "Frigid Fossil will hit T1 cold res 40% of the time, but it costs ~5c per attempt. Chaos spam at ~16 attempts average is cheaper."
- "Don't use essences here — Essence of Greed only gives +Life which you can get easier from the regular mod pool."

### Crafting Advice Principles

1. **Always check what's already on the item.** An item with 2 open prefixes and an existing bench craft might just need the bench craft removed and a better one applied.

2. **Bench craft is often the answer.** Before suggesting expensive crafting, check if a bench craft fills the need. It's deterministic and cheap.

3. **Compare methods by expected cost**, not just hit rate. Fossils have a higher per-attempt cost but often need fewer attempts. Use `simulate` to compare.

4. **Mod group names matter for simulation.** The `--target` flag uses CoE's internal mod group names (e.g., `IncreasedLife`, `ColdResistance`, `DefencesPercent`). Get these from `craft mods` output's `modgroup` field.

5. **Influence mods are powerful but narrow the pool.** Shaper/Elder/etc. mods can be build-defining. Always check if influence mods are relevant before recommending a crafting strategy.

6. **Consider the item's role in the build.** A helmet socketing GC with Hypothermia support needs specific pseudo-links. The crafting strategy should prioritize what the build actually needs (check the gems list for what's socketed there).

### Data Management
```bash
uv run pob craft update-data                       # Force refresh all CoE data (auto-cached with TTL)
uv run pob craft prices                            # Live currency prices from poe.ninja via CoE
```

Data is cached in `~/.cache/pob-mcp/coe/` with automatic TTL-based refresh (2 weeks for mod data, 4 hours for prices).

## Build File Location
- PoB installation: check `uv run pob engine info` for the path
- Build files are auto-detected from the standard PoB builds directory

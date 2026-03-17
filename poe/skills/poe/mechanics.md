# PoE Mechanics Reference

Quick reference for interpreting build stats, evaluating defenses, and giving actionable advice. Every section is designed to help you make recommendations, not just explain concepts.

## Stat Thresholds

Scan this first when reviewing `poe build stats` or `poe build validate` output:

| Stat | Red Flag | Acceptable | Good | Great |
|------|----------|------------|------|-------|
| Life (non-CI) | <3000 | 4000+ | 5000+ | 6000+ |
| ES (CI builds) | <6000 | 8000+ | 10000+ | 12000+ |
| Ele Resists | <75% | 75% | +30 overcap | +50 overcap |
| Chaos Resist | negative | 0%+ | 40%+ | 75% |
| Spec:LifeInc | <100% | 130%+ | 150%+ | 170%+ |
| Spell Suppression | 1-99% = BAD | 0% or 100% | 100% | 100% |
| PhysMaxHitTaken | <5000 | 6000+ | 8000+ | 10000+ |
| Hit Chance (attacks) | <90% | 95%+ | 100% | — |
| Move Speed | 0% | 25%+ | 30%+ | — |

## Interpreting Stats

**Offensive:** `TotalDPS`/`CombinedDPS` (single-skill), `FullDPS` (all skills marked for full DPS), `AverageHit`, `CritChance`/`CritMultiplier`, `Speed`, `HitChance`

**Defensive:** `Life`, `EnergyShield`, `TotalEHP`, `FireResist`/`ColdResist`/`LightningResist` (cap 75%), `ChaosResist` (default -60%), `FireResistOverCap` etc., `Armour`, `Evasion`, `EffectiveBlockChance`/`EffectiveSpellBlockChance`, `EffectiveSpellSuppressionChance`, `PhysicalMaximumHitTaken`, `Spec:LifeInc` (% life from tree)

### DPS Benchmarks (Shaper/Guardian config)

| DPS | Content Tier |
|-----|-------------|
| 200K | White/yellow maps |
| 500K | Red maps comfortable |
| 2M | Conquerors, Elder guardians |
| 5M | Sirus, Maven, Uber Elder |
| 15M+ | Uber bosses |
| 50M+ | Deep delve, instant-phase territory |

Compare builds using the SAME config. A build showing 10M with `conditionEnemyShocked` + all charges may be 3M realistic.

## Damage

### Scaling Types

- **"More"** multipliers are multiplicative (huge value). **"Increased"** is additive (diminishing returns).
- Each support gem typically provides a "more" multiplier — a 6th link is often 30-40% more DPS.
- **Flat damage** (e.g. "adds 10-20 fire damage") is most effective when you have lots of "increased" and "more" already.

### Conversion Pipeline

- Chain: Physical → Lightning → Cold → Fire → Chaos (one-directional, never backward)
- Converted damage benefits from modifiers to BOTH the original and final type
- 100% conversion = focused scaling + eliminates reflected damage of original type
- Common setups: Phys→Cold (Hatred + Hrimsorrow/cold mastery), Phys→Lightning (Wrath + Phys-to-Lightning Support), Phys→Fire (Avatar of Fire + Chieftain)
- Overcapped conversion (e.g. 50% phys-to-cold + 60% phys-to-fire = 110%) is normalized proportionally — no damage is lost

### Penetration, Exposure, and Resistance Reduction

These are SEPARATE categories and all stack:

| Category | Source Examples | Boss Effectiveness |
|----------|---------------|-------------------|
| **Penetration** | Support gems, tree nodes, ascendancy | Full — only applies to YOUR hits |
| **Exposure** | Wave of Conviction (-15%), Frost Bomb (-15%), masteries | Full — default -10%, source-specific values vary. Only strongest per element applies. |
| **Curse -res** | Flammability, Frostbite, Conductivity, Despair | Reduced on bosses (33% less on map bosses, 66% less on pinnacle pre-3.20; removed in 3.20 with rebalanced gem values) |
| **"Nearby enemies -X% res"** | Influenced helmet mods, auras | Full — always full strength |

For boss DPS, penetration and "nearby -res" gear mods are most reliable since curses are heavily reduced.

### Crit vs Non-Crit

- Crit needs 60%+ effective crit chance to justify investment. Below ~50%, scale hit damage or DoT instead.
- Effective crit = base crit × increased crit chance. Many skills have low base crit (5%) making crit expensive.
- Crit multi has diminishing returns once above ~500%. Better to invest in other multipliers.
- Elemental Overload (keystone): 40% more elemental damage for 8 seconds after you crit. Crits deal no extra damage and cannot inflict elemental ailments. Good for low-crit builds that can still proc it (~30%+ crit). Not useful for non-elemental or ailment-based builds.

### Damage over Time

- DoT does not hit, so it ignores accuracy, crit, and many on-hit effects.
- Ailment DoTs (ignite, poison, bleed) scale from hit damage. Non-ailment DoTs (e.g. Caustic Arrow ground) scale independently.
- Poison and bleed can stack. Ignite does not stack (only strongest applies).

### Gem Levels

- Level 20 + quality 20 is standard endgame. GCP recipe: level 20 gem + GCP = level 1 / quality 20.
- +1 to gem level is often 10-15% more damage for spell gems. Very efficient scaling.
- Empower Support adds raw levels — strongest in setups that already have +gem level gear.
- Awakened gems are strict upgrades over regular versions with additional properties at high levels.

## Defenses

### Resistances

- **Elemental resists**: must cap at 75%. Overcap 30-50% for curses and map mods (Elemental Weakness map mod is -30% at level 20 post-3.20).
- **Chaos resist**: starts at -60%. Getting to 0% is a massive survivability gain. 75% cap is luxury.
- **Maximum resistance** increases (e.g. Purity of Fire) are extremely powerful — each point above 75% is roughly 4% less elemental damage taken.

### Life and Energy Shield

- **Life pool**: 3000 bare minimum. 4000+ comfortable. 5000+ solid. Under 3000 = one-shots in endgame.
- `Spec:LifeInc` under 100% = red flag, needs more life nodes on tree.
- **CI (Chaos Inoculation)**: sets life to 1, makes you immune to chaos damage. Need high ES pool (8000+).
- **Low Life**: reserved life puts you below 50%. Enables Pain Attunement (30% more spell damage) but fragile without proper setup.
- **Hybrid (Life + ES)**: viable with Ghost Reaver or Eldritch Battery. ES acts as buffer over life.
- **Life recovery**: leech, regen, flasks, recoup. Leech is capped per instance and total. Regen has no cap.

### Mitigation Layers

- **Armour**: reduces physical damage taken. More effective against many small hits than few large hits. Formula: `reduction = armour / (armour + 5 * damage)`.
- **Evasion**: chance to avoid attacks entirely. Entropy-based (not purely random). Does NOT work against spells.
- **Block**: separate chance to avoid hits (attacks and/or spells). Capped at 75%.
- **Spell suppression**: 100% or don't invest at all. Halves spell damage taken. Partial investment is wasted points.
- **Endurance charges**: each gives 4% physical damage reduction and 4% all elemental resistances.
- **Fortification**: stacking buff, 1% less damage from hits per stack, max 20 stacks. Stacks gained depend on hit damage relative to enemy threshold — low-damage builds (DoT, minion) struggle to maintain full stacks. Primarily a melee mechanic (Champion gets permanent access).
- **Layers stack**: good builds combine 2-3 layers. Single-layer defense crumbles.

### Auras and Reservation

| Aura | Reservation | Effect | When to Use |
|------|-------------|--------|-------------|
| Determination | 50% | Flat + % armour | Near-mandatory for any build taking phys damage |
| Grace | 50% | Flat + % evasion | Evasion builds, pairs well with suppression |
| Defiance Banner | 10% | Armour + evasion, -crit damage taken | Almost always worth running — very cheap |
| Purity of Elements | 50% | All ele res + full ailment immunity | Fixes resist gaps AND replaces ailment immunity gear |
| Discipline | 35% | Flat ES + faster recharge | Core for CI and hybrid ES builds |
| Hatred | 50% | % phys as extra cold + more cold | Cold/phys conversion builds |
| Wrath | 50% | Flat lightning + more lightning | Lightning spell builds |
| Zealotry | 50% | Spell damage + crit + consecrated ground | Spell crit builds |
| Malevolence | 50% | DoT multi + skill duration | Core for DoT builds |
| Pride | 50% | Nearby enemies take more phys | Melee phys hit builds |
| Precision | Flat | Accuracy + crit chance | Attack builds (keep at low level for efficiency) |

**Heuristic:** If a build has low armour AND low evasion → check if Determination/Grace are equipped. If not, adding them is likely the single biggest defensive improvement available. The standard defensive package is Determination + Grace + Defiance Banner.

**Reservation math:** Without efficiency investment, you can fit one 50% aura + one 25% + banner. With Enlighten level 3-4 + tree nodes + gear, you can fit two 50% auras + banner + herald.

### Flasks

- **Endgame setup**: typically 1 life flask + 4 utility, or 0 life flasks if you have strong recovery (leech, regen, ES recharge)
- **Utility types**: Granite (armour), Jade (evasion), Basalt (phys reduction), Quicksilver (speed), Diamond (crit luck)
- **Critical suffixes**: "of Heat" (freeze immune), "of Staunching" (bleed immune), "of Warding" (curse immune), "of Grounding" (shock immune). Near-mandatory if not covered elsewhere.
- **Notable uniques**: Bottled Faith (consecrated ground + crit), Dying Sun (AoE + extra projectiles), Atziri's Promise (chaos leech + damage), Taste of Hate (phys-to-cold), Lion's Roar (melee + knockback)
- Pathfinder ascendancy makes flask uptime permanent — enables unique flask stacking strategies

### EHP and Maximum Hit Taken

- **TotalEHP** is the best single defensive metric — accounts for all mitigation layers.
- **PhysicalMaximumHitTaken**: if this is below 5000, physical one-shots from endgame bosses are likely.
- **Sirus Die Beam**: ~6800 total (multi-type: physical + elemental). **Shaper Slam**: ~8000 physical. These are community estimates. Uber versions deal ~40-60% more.

### Ailment and Stun Immunity

- **Freeze** is the most dangerous (complete lockout). Freeze immunity is near-mandatory.
- Sources: flask suffix "of Heat", Brine King pantheon, tree nodes, Purity of Elements aura, gear mods.
- **Stun**: not an ailment but similar. Stun immunity via Unwavering Stance, Kaom's Roots, or enough life.
- **Shock/Ignite**: less critical but still dangerous. Purity of Elements grants immunity to ALL elemental ailments.

## Charges

- **Power charges** (max 3): +40% increased crit chance each (pre-3.25; +200% in 3.25+). Generated by Assassin's Mark, Power Charge on Crit Support, Assassin ascendancy.
- **Frenzy charges** (max 3): +4% more damage, +4% attack/cast speed each (pre-3.25). Generated by Blood Rage, Frenzy skill, Raider ascendancy.
- **Endurance charges** (max 3): +4% phys damage reduction, +4% all ele resist each (pre-3.25; ele resist changed to ele damage reduction in 3.25). Generated by Enduring Cry, Juggernaut ascendancy.
- **Config check**: if `useFrenzyCharges=true` in PoB config, verify the build has a reliable generation method. Otherwise DPS is inflated by ~12%.

## Ascendancy Quick Reference

| Ascendancy | Identity | Typical Builds |
|------------|----------|----------------|
| Necromancer | Minions, offerings, +gem levels to minion gems | SRS, Spectres, Skeletons |
| Elementalist | Elemental damage, golems, exposure | Ignite, ele hit, golem stacker |
| Occultist | Curses, ES, cold/chaos DoT, power charges | Cold DoT, curse builds, CI |
| Juggernaut | Armour, endurance charges, stun immune, accuracy | RF, tanky melee, lab runner |
| Berserker | Raw damage, warcries, rage | Slam skills, high-damage melee |
| Chieftain | Fire conversion, totems, life regen | Fire melee, totems |
| Deadeye | Projectiles, tailwind, far shot | Bow builds, projectile spells |
| Raider | Frenzy charges, phasing, onslaught, elemental avoidance | Fast mappers, ele attack |
| Pathfinder | Flask uptime, poison, nature | Flask builds, poisoners |
| Champion | Permanent Fortify, aura effect, impale | Tanky attack builds, impale |
| Gladiator | Block, bleed, challenger charges | Max block, lacerate bleed |
| Slayer | Overleech, cull, crit | Cyclone, melee crit |
| Assassin | Crit, poison, elusive | CoC, crit stacker, poison |
| Trickster | Hybrid defenses (ES+evasion), DoT | DoT, hybrid ES/life |
| Saboteur | Traps, mines, blind, regen per device | Mine/trap builds |
| Inquisitor | Ignore enemy resists on crit, consecrated ground, battlemage | Crit spells, battlemage |
| Hierophant | Totems, mana, arcane surge, brands | Totem builds, mana stacker |
| Guardian | Aura support, ES, minion hybrid | Aura bot, support, minion hybrid |
| Ascendant | Mix two mini-ascendancies, extra jewel socket | Flexible, aura stackers |

## Passive Tree

- 122-123 points at level 100 (99 from levels, 23-24 from quests including bandit choice)
- **Keystones** define build identity (CI, Resolute Technique, Point Blank, Elemental Overload, Iron Will, Ghost Dance)
- **Notable passives** are the named nodes — most of a build's power comes from these
- **Jewel sockets** hold regular, abyss, cluster, or timeless jewels — often more efficient than tree nodes
- **Cluster jewels**: extend the tree with custom notable passives. Large (8-12 passives), Medium (4-6), Small (2-3).
- **Mastery nodes**: each mastery group offers a choice of bonuses. Can only pick one per mastery type.
- **Anointments**: apply a notable passive to an amulet via Blight oils. Effectively a free passive point for hard-to-reach nodes.
- **Timeless jewels**: transform nodes in their radius. Each seed number gives different results.

## Gem Links

- 6-link max: 1 active skill + 5 supports
- Supports must match skill tags (attack supports don't work with spells)
- **Socket colors**: tied to base stat requirements (STR=red, DEX=green, INT=blue).
- **Link order doesn't matter** — only which gems are linked together.
- **Trigger setups**: Cast when Damage Taken, Cast on Crit, Arcanist Brand — automate secondary skills.
- **Aura/reservation**: auras reserve mana/life permanently. See "Auras and Reservation" section above.

## Item System

### Prefix / Suffix Rules

**Magic**: max 1 prefix + 1 suffix. **Rare**: max 3 prefixes + 3 suffixes. **Jewels**: max 2 + 2.

| Typical Prefixes | Typical Suffixes |
|-----------------|-----------------|
| +# to maximum Life | +#% to Fire/Cold/Lightning/Chaos Resistance |
| +# to maximum ES | #% increased Attack Speed |
| % increased Armour/Evasion/ES | #% increased Critical Strike Chance |
| Adds # to # physical/ele damage | +#% to Critical Strike Multiplier |
| +1 to Level of X Gems | +# to Strength/Dexterity/Intelligence |
| % increased Spell Damage | #% increased Movement Speed (boots only) |

**Crafted mods** (bench) count toward affix limits. "Open prefix" = can bench craft life or damage. "Open suffix" = can bench craft resist or speed.

Use `poe sim analyze` to see open slots on equipped items.

### Item Level (ilvl) Gating

- Higher ilvl unlocks higher mod tiers. ilvl 84+ unlocks T1 for most mods. ilvl 86 for influenced T1.
- Below ilvl 75 = many top tiers locked out. Always check with `poe sim mods --ilvl`.
- Lower ilvl can be DESIRABLE for crafting when you want fewer possible mods (smaller pool = higher chance of hitting target).

### Mod Weighting and Groups

- Each mod has a **spawn weight** for each item base. Higher weight = more likely to roll.
- Mods belong to **mod groups** — you cannot roll two mods from the same group on one item (e.g., two different flat life prefixes).
- Fossils multiply weights of mods with matching tags (more likely) and can zero-out weights (block entirely).
- Essences guarantee one specific mod and randomize the rest — the guaranteed mod ignores normal weighting.

### Crafting Methods — When to Use What

| Situation | Method | Why |
|-----------|--------|-----|
| Need one specific mod guaranteed | Essence | Guarantees one mod, randomizes rest |
| Need mods from specific tags | Fossil (in resonator) | Multiplies/blocks mod weights by tag |
| Need one prefix OR suffix on magic | Alt + Aug + Regal | Cheap, targeted for 1-2 mod items |
| Rerolling a rare for multiple mods | Chaos (last resort) | Unweighted — expect hundreds of attempts |
| Good prefixes, bad suffixes | "Prefixes cannot be changed" + Scour | Wipes suffixes, keeps prefixes. Then craft new suffixes. |
| Want to add one mod to a finished rare | Exalted Orb (or influenced exalt) | Adds 1 random mod. Risky but powerful with metamods. |
| Comparing craft cost vs market price | `poe ninja price check` | Always check before committing expensive currency |

### Metamod Crafting

Metamods are bench crafts that protect or restrict mods during other crafting operations:

| Metamod | Affix | Effect |
|---------|-------|--------|
| "Prefixes cannot be changed" | Suffix | Protects all prefixes during scour, chaos, harvest reforge, annul |
| "Suffixes cannot be changed" | Prefix | Protects all suffixes during same operations |
| "Can have up to 3 crafted modifiers" | Suffix | Allows bench-crafting 3 mods instead of 1 (multimod) |
| "Cannot roll Attack modifiers" | Suffix | Blocks all attack-tagged mods from rolling |
| "Cannot roll Caster modifiers" | Suffix | Blocks all caster-tagged mods from rolling |

**Key strategies:**
- **Prefix lock + scour**: "Prefixes cannot be changed" → Orb of Scouring = removes all suffixes, keeps prefixes. Then craft new suffixes.
- **Multimod finish**: craft "multimod" + 2 other bench crafts to fill an item cheaply (uses 3 suffix/prefix slots total).
- **Cannot roll X + exalt**: block a mod category, then exalted orb can only add from the remaining pool. Narrows outcomes.
- Fossils and essences CANNOT be used with metamods active.

### Influence and Special Items

- **Influence types**: Shaper, Elder, Crusader, Hunter, Redeemer, Warlord, Searing Exarch, Eater of Worlds
- Influenced items can roll exclusive mods not available on normal items
- **Awakener's Orb**: combines two differently-influenced items. Keeps one influenced mod from each, rerolls rest.
- **Fractured items**: one mod is permanently locked (cannot be changed by any crafting). Ideal base for deterministic crafting.
- **Eldritch currency** (Ichors, Embers, Orbs of Conflict): modify implicit mods on non-influenced items. Separate system from explicit mods.

### Slot Priorities for Upgrades

When asked "what should I upgrade next?":

1. **Weapon**: biggest DPS impact. Flat phys/ele for attacks, +gem levels/spell damage for spells.
2. **Body Armour**: highest base defenses, 6-link home. Life/ES + base defenses.
3. **Amulet**: most flexible offensive slot. Crit multi, +gem levels, attributes. Anointment slot.
4. **Rings**: fix resist/attribute gaps + damage mods. Curse on hit is premium.
5. **Helmet**: life + resists. Influenced: -9% nearby res, conc/AoE effect, +gem levels.
6. **Boots**: movement speed (25%+ required) + life + resists. Tailwind/Elusive are premium.
7. **Gloves**: life + resists + attack speed or added damage. Strike additional target (Hunter) is build-defining.
8. **Belt**: life + resists + flask/recovery. Stygian Vise (abyssal socket) is best generic base.

## PoB Config Reality Check

Stats change dramatically based on config. Always verify:

- **Frenzy/Power/Endurance charges**: only realistic if build has a generation source. Enabling all three without generation inflates DPS by ~30-40%.
- **Flask active**: reasonable for mapping, questionable for long boss fights unless Pathfinder.
- **Enemy boss type**: "None" = no enemy resistances (mapping DPS). "Shaper" = realistic boss DPS with enemy res applied.
- **conditionEnemyShocked** without reliable shock source = 15-50% free damage.
- **Custom mods**: can add anything. Always check `poe build config get` for custom entries.

Use the "boss" or "sirus" config preset for realistic bossing DPS comparisons.

## Boss Reference

| Boss Tier | Ele Resist | Chaos Resist | Curse Effect (pre-3.20) | Curse Effect (3.20+) |
|-----------|-----------|-------------|------------------------|---------------------|
| Map monsters | 0% | 0% | 100% | 100% |
| Map bosses | 30% | 15% | 67% (33% less) | 100% (penalty removed) |
| Guardians / Conquerors | 40% | 25% | 34% (66% less) | 100% (penalty removed) |
| Pinnacle (Sirus/Maven/UE) | 50% | 30% | 34% (66% less) | 100% (penalty removed) |

Note: Boss resistance values are approximate community-sourced numbers. Post-3.20, curse penalties were removed but gem values were rebalanced lower to compensate.

## Validation Fix Quick Reference

When `poe build validate` flags issues, here are the fastest fixes:

| Flag | Priority Fixes |
|------|---------------|
| Ele resist uncapped | Bench craft resist on open suffix → swap a ring → blessed orb existing res |
| Chaos resist negative | Craft on belt/ring suffix. Purity of Elements frees suffixes for chaos res |
| Life pool low | More tree nodes (target Spec:LifeInc 150%+) → life prefix on gear |
| Suppression partial (1-99%) | Either cap it (dex-base gear, tree nodes near Shadow/Ranger) or drop it entirely |
| No freeze immunity | Flask "of Heat" → Brine King pantheon → Purity of Elements |
| Stun vulnerability | Unwavering Stance keystone → Kaom's Roots → 100% stun avoidance |
| Attributes unmet | +30 attribute bench craft → amulet implicit → tree nodes |
| Mana cost > regen | -mana cost craft on rings (-7 each) → Lifetap Support → Inspiration Support |
| Movement speed 0% | Movement speed suffix on boots (bench craft if open) |
| Missing flasks | Add utility flasks with ailment immunity suffixes |

## Dangerous Map Mods

- **Elemental reflect**: instant death for most ele builds. Need "reflected damage cannot kill you" or Elementalist ascendancy.
- **-max resistance**: each point below 75% = ~4% more ele damage taken. This is why overcapping matters.
- **No regen**: breaks builds reliant on mana/life regen. Need leech, flasks, or Eldritch Battery.
- **Elemental Weakness curse**: -30% to all elemental resists (level 20 post-3.20). Map mod version uses lower gem level (-15%). This is why 30-50% overcap is recommended.
- **Extra damage as element**: stacks with other sources, can make otherwise safe maps lethal.

## Common Build Archetypes

- **League starter**: cheap to gear, works on low budget, scales with investment. Examples: SRS, Toxic Rain, Boneshatter.
- **Boss killer**: high single-target DPS, enough defenses to survive boss mechanics. Often sacrifice clear speed.
- **Mapper/farmer**: fast movement, good AoE clear, high item quantity/rarity. Often glass cannon.
- **All-rounder**: balanced build that can do most content. Usually more expensive than specialists.

## Endgame Progression

1. **Maps** (tier 1-16): core endgame content loop
2. **Atlas completion**: unlocking and completing all maps for atlas passive points
3. **Pinnacle bosses**: Sirus, Maven, Uber Elder, The Feared — require specific builds
4. **Uber bosses**: harder versions of pinnacle bosses with better loot. Require optimized builds.
5. **Delve**: infinite depth dungeon. Deeper = harder + more rewarding. Separate leaderboard (depthsolo on poe.ninja).

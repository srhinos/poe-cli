# poe-cli

Interact with all your favorite PoE tools through the command line. Built on [Path of Building Community](https://github.com/PathOfBuildingCommunity/PathOfBuilding) — parses build XML files and runs PoB's actual Lua calculation engine in-process via [lupa](https://github.com/scoder/lupa).

## Install

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv tool install git+https://github.com/srhinos/poe-cli
```

This puts `poe` on your PATH. Verify with:

```bash
poe --help
```

### Claude Code skills (optional)

If you use [Claude Code](https://docs.anthropic.com/en/docs/claude-code), install the skill so Claude knows how to use the CLI:

```bash
poe install-skill
```

This copies skill files into `~/.claude/skills/poe/`. After upgrading the CLI, re-run:

```bash
poe install-skill --force
```

Options: `--force` (overwrite existing), `--symlink` (symlink instead of copy, for development), `--uninstall` (remove).

## Commands

### Builds

```bash
# Read and analyze
poe build list
poe build summary "My RF Jugg"
poe build analyze "My RF Jugg"
poe build stats "My RF Jugg" --category off
poe build validate "My RF Jugg"
poe build compare "My RF Jugg" "League Starter"

# Drill into loadouts
poe build tree get "My RF Jugg"
poe build items list "My RF Jugg"
poe build gems list "My RF Jugg"
poe build flasks list "My RF Jugg"
poe build jewels list "My RF Jugg"
poe build config get "My RF Jugg"

# Modify builds (writes go to Claude/ subfolder)
poe build create "New Build" --class-name Witch --ascendancy Necromancer --level 90
poe build duplicate "My RF Jugg" "RF Jugg Copy"
poe build rename "Old Name" "New Name"
poe build set-level "My RF Jugg" --level 95
poe build set-class "My RF Jugg" --class Witch --ascendancy Necromancer
poe build items add "My RF Jugg" --slot Helmet --base "Hubris Circlet" --rarity RARE
poe build items edit "My RF Jugg" --slot Helmet --add-explicit "+90 to maximum Life"
poe build gems add "My RF Jugg" --slot "Body Armour" --gem Fireball --gem "Spell Echo Support"
poe build tree set "My RF Jugg" --add-nodes 500,600
poe build flasks add "My RF Jugg" --base "Granite Flask" --slot "Flask 1"
poe build jewels add "My RF Jugg" --base "Cobalt Jewel" --slot "Jewel 1"
poe build config preset "My RF Jugg" --preset boss

# Import/export and sharing
poe build decode <build_code>
poe build encode "My RF Jugg"
poe build share "My RF Jugg"
poe build import <url_or_code> --name "Imported"
```

### Crafting

```bash
poe sim search "Crown"
poe sim mods "Hubris Circlet" --ilvl 84
poe sim weights "Hubris Circlet" --ilvl 84
poe sim simulate "Vaal Regalia" --method fossil --target IncreasedLife --fossils "Pristine Fossil,Dense Fossil"
poe sim simulate-multistep "Vaal Regalia" --step alteration --step regal --target IncreasedLife
poe sim compare "Vaal Regalia" --target IncreasedLife --fossils "Pristine Fossil"
poe sim suggest --mod "IncreasedLife"
poe sim analyze "My RF Jugg" --slot Helmet
poe sim prices
```

### Economy (poe.ninja)

```bash
poe ninja price check "Exalted Orb" Currency
poe ninja price list Currency
poe ninja price convert 10 "Exalted Orb" "Chaos Orb"
poe ninja price history "Exalted Orb" Currency
poe ninja meta summary
poe ninja builds search --class Necromancer --skill "Summon Raging Spirits"
poe ninja builds inspect <account> <character>
poe ninja atlas recommend
```

All commands output JSON. Add `--human` for readable output.

### Live engine

```bash
poe build engine load "My RF Jugg"
poe build engine stats
```

Embeds LuaJIT via lupa and runs PoB's actual calculation code in-process.

## Build safety

All write operations go to a `Claude/` subfolder inside the PoB builds directory. Your original builds are never modified. The `--file` flag bypasses this and writes directly to the specified path.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- Path of Building Community (installed normally — needed for `poe build` commands)

## Development

```bash
git clone https://github.com/srhinos/poe-cli.git
cd poe-cli
uv sync

uv run ruff check poe/ tests/                                # Lint
uv run ruff format --check poe/ tests/                       # Format check
uv run ty check poe/                                         # Type check
uv run pytest tests/ --ignore=tests/integration -v           # Unit tests
uv run pytest tests/ -v                                      # All tests (needs network + PoB)
```

## License

GPL-3.0

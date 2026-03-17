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
poe build analyze "Main GC"
poe build stats "Main GC" --category off
poe build validate "Main GC"
poe build compare "Main GC" "Backup GC"

# Drill into loadouts
poe build tree get "Main GC"
poe build items list "Main GC"
poe build gems list "Main GC"
poe build flasks list "Main GC"
poe build jewels list "Main GC"
poe build config get "Main GC"

# Modify builds (writes go to Claude/ subfolder)
poe build create "New Build" --class-name Witch --ascendancy Necromancer --level 90
poe build items add "Main GC" --slot Helmet --base "Hubris Circlet" --rarity RARE
poe build items edit "Main GC" --slot Helmet --add-explicit "+90 to maximum Life"
poe build gems add "Main GC" --slot "Body Armour" --gem Fireball --gem "Spell Echo Support"
poe build tree set "Main GC" --add-nodes 500,600

# Import/export and sharing
poe build decode <build_code>
poe build encode "Main GC"
poe build import <url_or_code> --name "Imported"
```

### Crafting

```bash
poe sim search "Crown"
poe sim mods "Hubris Circlet" --ilvl 84
poe sim simulate "Vaal Regalia" --method fossil --target IncreasedLife --fossils "Pristine Fossil,Dense Fossil"
poe sim analyze "Main GC" --slot Helmet
poe sim prices
```

All commands output JSON. Add `--human` for readable output.

### Live engine

```bash
poe build engine load "Main GC"
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

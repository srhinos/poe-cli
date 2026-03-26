# pob-mcp

A Python CLI for interacting with [Path of Building](https://github.com/PathOfBuildingCommunity/PathOfBuilding) builds. Parses build XML files and runs PoB's actual Lua calculation engine in-process via [lupa](https://github.com/scoder/lupa).

Designed to work as a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill — Claude learns the CLI commands and calls them to analyze your builds.

**[Buy me a coffee](https://buymeacoffee.com/ianderse)** if you find this useful.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Path of Building Community (installed normally)

## Install

```bash
git clone https://github.com/ianderse/pob-mcp.git
cd pob-mcp
uv sync
```

## Usage

```bash
uv run pob builds list
uv run pob builds analyze "Main GC"
uv run pob builds stats "Main GC" --category off
uv run pob builds compare "Main GC" "Leaguestart GC"
uv run pob builds validate "Main GC"

uv run pob engine load "Main GC"     # live stats via PoB's Lua engine
uv run pob engine info

uv run pob tree get "Main GC"
uv run pob items list "Main GC"
uv run pob gems list "Main GC"
uv run pob config get "Main GC"
```

All commands output JSON. Add `--human` for readable output.

## How it works

**XML parsing** (`builds analyze`, `stats`, `validate`, etc.) reads PoB's `.xml` build files directly — no engine needed, instant results.

**Live engine** (`engine load`, `engine stats`) embeds LuaJIT via lupa and runs PoB's actual calculation code in-process. Same math as the PoB GUI, just headless.

## Claude Code skill

The `skills/pob.md` file teaches Claude how to use the CLI. Drop this repo in your project and Claude will know how to analyze builds, check defenses, compare setups, etc.

## License

GPL-3.0

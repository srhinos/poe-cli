# Architecture

## Directory Structure

```
poe/
├── app.py                    # CLI entry point (cyclopts App)
├── constants.py              # Global constants (CLAUDE_SUBFOLDER, POB_XML_EXTENSION)
├── types.py                  # Shared enums (Rarity, Influence, CraftMethod, etc.)
├── exceptions.py             # PoeError hierarchy (BuildNotFoundError, SlotError, etc.)
├── output.py                 # JSON/human output rendering with formatter registry
├── paths.py                  # Build file discovery, path resolution, safety validation
├── safety.py                 # Clone-on-write safety layer (Claude/ subfolder)
├── formatters.py             # Human formatter registrations
│
├── commands/                 # CLI commands (cyclopts subcommands)
│   ├── root.py               #   install-skill
│   ├── build/                #   poe build ... (list, create, analyze, stats, items, gems, tree, etc.)
│   ├── ninja/                #   poe ninja ... (price, builds, atlas, meta)
│   ├── sim/                  #   poe sim ... (mods, tiers, simulate, suggest)
│   └── dev/                  #   poe dev ... (development utilities)
│
├── models/                   # Pydantic data models (no business logic)
│   ├── build/                #   BuildDocument, Item, Gem, TreeSpec, BuildConfig, etc.
│   ├── ninja/                #   CurrencyLine, BuildSummary, LeagueIndexState, etc.
│   └── sim.py                #   Mod, Fossil, Essence, SimulationResult, etc.
│
├── services/                 # Business logic layer
│   ├── build/                #   BuildService, ItemsService, GemsService, TreeService, etc.
│   │   ├── xml/              #     XML parser (SafeET → BuildDocument) and writer
│   │   └── engine/           #     PoB Lua runtime via lupa (LuaJIT stat calculation)
│   ├── ninja/                #   NinjaClient, EconomyService, BuildsService, AtlasService
│   └── repoe/                #   RepoEData (mod pools), CraftingEngine (Monte Carlo sim)
│       └── pipeline/         #     Dev-only data ingestion from RePoE subtree
│
├── data/repoe/               # Bundled game data (JSON, read-only at runtime)
│   ├── base_items.json       #   Item bases with properties
│   ├── mods.json             #   All game mods with spawn weights
│   ├── mod_pool.json         #   Base → mod mappings
│   ├── fossils.json          #   Fossil data
│   ├── essences.json         #   Essence data
│   └── bench_crafts.json     #   Crafting bench options
│
└── skills/poe/               # Claude Code skill files (MCP interface docs)
    ├── SKILL.md, build.md, craft.md, ninja.md, mechanics.md

vendor/RePoE/                 # Vendored RePoE data extraction tool (subtree, not HTTP)
tests/                        # Test suite (mirrors poe/ layout)
```

## Layered Architecture

```
Commands → Services → Models → Data
```

- **Commands** (`poe/commands/`) handle CLI args, call services, render output. No business logic.
- **Services** (`poe/services/`) contain all business logic. Each service operates on models.
- **Models** (`poe/models/`) are Pydantic data containers. No logic, no methods beyond validation.
- **Data** is either XML files (PoB builds) or bundled JSON (`poe/data/repoe/`).

Never skip a layer. Commands must not import from `xml/` or `data/` directly — always go through a service.

## Key Data Flows

### Build Read

```
Command → BuildService.load()
        → paths.resolve_build_file()    # find XML on disk
        → xml/parser.py                 # SafeET XML → BuildDocument
        → output.render()               # JSON to stdout
```

### Build Write (Clone-on-Write)

```
Command → Service (e.g., ItemsService.edit())
        → safety.resolve_for_write()    # clone to Claude/ if needed
        → mutate BuildDocument
        → xml/writer.py                 # BuildDocument → XML file
        → return MutationResult         # includes cloned_from field
```

Write operations use `safety.resolve_for_write()` which copies the original build into a `Claude/` subfolder before modifying. This prevents accidental damage to user's real builds. Reads prefer `Claude/` copies over originals for read-after-write consistency. The safety layer is bypassed when `--file-path` is explicitly provided.

### Crafting Simulation

```
Command → SimService.simulate()
        → RepoEData loads mod pools     # from bundled JSON
        → CraftingEngine                # Monte Carlo iterations
        → SimulationResult
```

### Economy (poe.ninja)

```
Command → EconomyService
        → NinjaClient                   # httpx + rate limiting
        → poe.ninja API
        → cached in ~/.cache/poe/
```

## Output Pattern

All commands output JSON by default. Human-readable formatters are registered via `@human_formatter(ModelClass)` decorator in `formatters.py`. Commands call `output.render(data, human=flag)`. Errors serialize as `{"error": "..."}` to stderr via `poe/app.py`.

## Environment Variables

- `POB_PATH` — Path of Building installation directory (auto-detected from `%APPDATA%`)
- `POB_BUILDS_PATH` — Builds directory (auto-detected from `~/Documents/Path of Building/Builds`)

## Key Models

**Build domain:** `BuildDocument` (central domain object), `Item`, `Gem`/`GemGroup`, `TreeSpec`, `BuildConfig`, `MutationResult`

**Ninja domain:** `CurrencyLine`, `BuildSummary`, `LeagueIndexState`

**Sim domain:** `Mod`, `ModTier`, `Fossil`, `Essence`, `SimulationResult`

**Shared enums** (`poe/types.py`): `Rarity`, `Influence`, `CraftMethod`, `MatchMode`, `StatCategory`, `QualityId`

**Exceptions** (`poe/exceptions.py`): `PoeError` (base), `BuildNotFoundError`, `SlotError`, `EngineNotAvailableError`, `SimDataError`, `BuildValidationError`, `CodecError`

## RePoE Data Pipeline

The `pipeline/` package under `poe/services/repoe/` is a **dev-only** tool. It ingests raw data from the vendored `vendor/RePoE/` subtree and produces the bundled JSON files in `poe/data/repoe/`. This pipeline never runs at runtime — users consume pre-built JSON.

The RePoE data is vendored as a git subtree, never fetched over HTTP.

## Test Infrastructure

Test fixtures live in `tests/conftest.py`:

- `invoke_cli(app, args)` → `CliResult` with `.output`, `.exit_code`, `.exception`
- `MINIMAL_BUILD_XML` — complete PoB XML string for constructing test builds
- `PoBXmlBuilder` — fluent builder: `PoBXmlBuilder(tmp_path).with_class("Witch").with_item("Helmet", ...).write()`
- `make_repoe_data()` / `REPOE_DATA` — mock RepoE data dict for crafting tests
- `fixture_path()` — resolve files from `tests/fixtures/`

HTTP mocking uses `respx` for ninja service tests. Integration tests requiring real PoB or network are marked `@pytest.mark.integration`.

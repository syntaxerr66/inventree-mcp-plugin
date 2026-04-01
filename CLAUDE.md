# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Django plugin for [InvenTree](https://inventree.org/) that exposes inventory operations as MCP (Model Context Protocol) tools over Streamable HTTP transport. It runs **inside** InvenTree's Django process with direct ORM access — no REST API round-trips.

## Development Setup

```bash
pip install -e .
```

There is no test suite, linter configuration, or CI pipeline. The plugin is tested by installing it into a running InvenTree instance and exercising the MCP endpoint.

## Architecture

### Plugin Registration

InvenTree discovers the plugin via the `[project.entry-points."inventree_plugins"]` entry in `pyproject.toml`, which points to `InvenTreeMCPPlugin` in `plugin.py`. The plugin class uses InvenTree's `UrlsMixin` and `SettingsMixin` to register the `/plugin/inventree-mcp/mcp` URL endpoint and expose Google API settings.

### Request Flow

1. **`views.py`** — `MCPView` extends `django-mcp-server`'s `MCPServerStreamableHttpView`. It lazily configures InvenTree's auth classes (token, session, basic) in `as_view()` and stores the authenticated user in thread-local context during `dispatch()`.
2. **`context.py`** — Thread-local storage (`threading.local`) that passes the authenticated Django user from the DRF view layer into MCP tool functions. Tools that need user context (stock operations) call `get_current_user()`.
3. **`mcp_server.py`** — Creates the singleton `DjangoMCP` instance with server `instructions` (returned by the auto-registered `get_server_instructions` tool). Tool modules import `mcp` from here and register via `@mcp.tool()`.
4. **`tools/__init__.py`** — Imports all tool modules to trigger `@mcp.tool()` registration. This import is triggered by `views.py` at startup.

### Tool Pattern

Every tool follows the same structure:
- Async function decorated with `@mcp.tool()`
- Inner `@sync_to_async` function that performs Django ORM operations
- **Lazy imports** of Django models inside the inner function (avoids import-time app registry issues)
- Returns JSON strings via `serializers.to_json()`

Tool modules: `parts.py` (7 tools), `stock.py` (7 tools), `locations.py` (5 tools, +location_type support), `categories.py` (4 tools), `parameters.py` (13 tools — templates, part params incl. bulk upsert, category params, location types).

### Key Conventions

- `id=0` or `parent=0` means "not set" / "no filter" (not a real FK value)
- `Optional[bool] = None` means "don't change this field" in create/update tools
- Serializers in `serializers.py` have full and compact variants. List/search tools use `*_compact` serializers (fewer fields) to reduce MCP response size; `get_*` tools use full serializers. `to_json()` produces compact JSON (no whitespace)
- Icon validation (`icons.py`) loads InvenTree's bundled `icons.json` with `@lru_cache` and validates `ti:<name>:<variant>` format, with fuzzy suggestions on invalid names

### Dependencies

- `django-mcp-server>=0.4.0` — provides `DjangoMCP` and `MCPServerStreamableHttpView`
- `requests` — used only for Google Custom Search image lookup
- InvenTree's Django models (`part.models`, `stock.models`, `common.models`, `users.authentication`) are imported lazily at call time

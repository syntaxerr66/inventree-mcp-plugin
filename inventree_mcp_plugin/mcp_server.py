"""DjangoMCP server instance for the InvenTree MCP plugin.

Tool modules import `mcp` from here and register tools via @mcp.tool() decorator.
The views module imports tools/ to trigger registration at startup.
"""

from mcp_server.djangomcp import DjangoMCP

_INSTRUCTIONS = """\
InvenTree MCP Server — inventory management via direct ORM access.

## Important conventions
- ID parameters of 0 mean "no filter" or "top-level" (not a real database ID).
- Use search tools BEFORE creating new items to avoid duplicates.
- Search/list tools return 10 results by default. The `count` field shows the \
total number of matches. Increase `limit` or paginate with `offset` to see more.
- Search/list tools return compact results. Use get_part, get_stock_location, \
or get_stock_item for full detail on a specific item.

## Parameter templates
Before creating a parameter template, call `list_parameter_templates` to check \
if one already exists. Reuse existing templates rather than creating near-duplicates \
(e.g. don't create "External Diameter" when "Outer Diameter (OD)" already exists).

## Bulk operations
Use `bulk_set_part_parameters` when setting parameters on multiple parts — it \
performs a single database transaction instead of one call per parameter.
"""

mcp = DjangoMCP(name="inventree-mcp", instructions=_INSTRUCTIONS, stateless=True)

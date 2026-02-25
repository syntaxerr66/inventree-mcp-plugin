"""DjangoMCP server instance for the InvenTree MCP plugin.

Tool modules import `mcp` from here and register tools via @mcp.tool() decorator.
The views module imports tools/ to trigger registration at startup.
"""

from mcp_server.djangomcp import DjangoMCP

mcp = DjangoMCP(name="inventree-mcp")

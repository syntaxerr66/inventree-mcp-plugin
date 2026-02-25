"""InvenTree plugin class — registers the MCP endpoint and plugin settings."""

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, UrlsMixin


class InvenTreeMCPPlugin(UrlsMixin, SettingsMixin, InvenTreePlugin):
    """Plugin that exposes InvenTree operations as MCP tools over Streamable HTTP."""

    NAME = "InvenTree MCP"
    SLUG = "inventree-mcp"
    TITLE = "InvenTree MCP Server"
    DESCRIPTION = "Exposes InvenTree inventory operations as MCP tools"
    VERSION = "0.1.0"
    AUTHOR = "Chris Botelho"

    SETTINGS = {
        "GOOGLE_API_KEY": {
            "name": "Google API Key",
            "description": "API key for Google Custom Search (optional, for image search)",
            "default": "",
        },
        "GOOGLE_CSE_ID": {
            "name": "Google CSE ID",
            "description": "Custom Search Engine ID for image search (optional)",
            "default": "",
        },
    }

    def setup_urls(self):
        from django.urls import re_path
        from django.views.decorators.csrf import csrf_exempt

        from .views import MCPView

        return [
            re_path(r"^mcp/?$", csrf_exempt(MCPView.as_view()), name="mcp"),
        ]

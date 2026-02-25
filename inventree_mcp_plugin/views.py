"""Authenticated MCP Streamable HTTP endpoint for InvenTree.

Wraps django-mcp-server's view with DRF TokenAuthentication + SessionAuthentication.
"""

import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from mcp_server.views import MCPServerStreamableHttpView

from .context import set_current_user
from .mcp_server import mcp

# Trigger tool registration by importing the tools package
from . import tools  # noqa: F401

logger = logging.getLogger("inventree_mcp_plugin")


@method_decorator(csrf_exempt, name="dispatch")
class MCPView(MCPServerStreamableHttpView):
    """MCP endpoint with DRF authentication."""

    mcp_server = mcp

    def dispatch(self, request, *args, **kwargs):
        from rest_framework.authentication import (
            SessionAuthentication,
            TokenAuthentication,
        )
        from rest_framework.exceptions import AuthenticationFailed
        from rest_framework.request import Request as DRFRequest

        # Wrap in DRF request for authentication
        drf_request = DRFRequest(request)
        authenticated = False

        for auth_cls in [TokenAuthentication, SessionAuthentication]:
            try:
                result = auth_cls().authenticate(drf_request)
                if result is not None:
                    user, _ = result
                    request.user = user
                    set_current_user(user)
                    authenticated = True
                    break
            except AuthenticationFailed:
                continue

        if not authenticated and not getattr(request.user, "is_authenticated", False):
            return JsonResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "Authentication required. Use Token or Session auth.",
                    },
                    "id": None,
                },
                status=401,
            )

        return super().dispatch(request, *args, **kwargs)

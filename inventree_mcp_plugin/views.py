"""Authenticated MCP Streamable HTTP endpoint for InvenTree.

MCPServerStreamableHttpView inherits from DRF's APIView, so InvenTree's
default DRF permission/auth classes apply. We override them to use InvenTree's
own token auth and only require IsAuthenticated (no model permissions needed).
"""

import logging

from django.views.decorators.csrf import csrf_exempt
from mcp_server.views import MCPServerStreamableHttpView
from rest_framework.permissions import IsAuthenticated

from .context import set_current_user
from .mcp_server import mcp

# Trigger tool registration by importing the tools package
from . import tools  # noqa: F401

logger = logging.getLogger("inventree_mcp_plugin")


class MCPView(MCPServerStreamableHttpView):
    """MCP endpoint using InvenTree's auth and relaxed permissions."""

    mcp_server = mcp

    # Use InvenTree's token auth + session auth (no DjangoModelPermissions)
    authentication_classes = []  # Populated in setup to avoid import-time issues
    permission_classes = [IsAuthenticated]

    @classmethod
    def as_view(cls, **initkwargs):
        # Lazily set authentication classes from InvenTree's own auth
        from rest_framework.authentication import (
            BasicAuthentication,
            SessionAuthentication,
        )

        try:
            from users.authentication import ApiTokenAuthentication

            cls.authentication_classes = [
                ApiTokenAuthentication,
                SessionAuthentication,
                BasicAuthentication,
            ]
        except ImportError:
            cls.authentication_classes = [
                SessionAuthentication,
                BasicAuthentication,
            ]

        view = super().as_view(**initkwargs)
        view.csrf_exempt = True
        return csrf_exempt(view)

    def dispatch(self, request, *args, **kwargs):
        # Store user in thread-local for tool functions that need it
        if hasattr(request, "user") and getattr(
            request.user, "is_authenticated", False
        ):
            set_current_user(request.user)

        return super().dispatch(request, *args, **kwargs)

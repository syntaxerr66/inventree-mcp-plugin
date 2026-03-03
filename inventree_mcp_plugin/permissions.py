"""Role-based permission checks for MCP tools using InvenTree's permission system."""

import json
import logging
from typing import Optional

from asgiref.sync import sync_to_async

from .context import get_current_user

logger = logging.getLogger("inventree_mcp_plugin.permissions")


def require_permission(role: str, action: str) -> Optional[str]:
    """Check if the current user has the required role permission.

    Returns None if allowed, or a JSON error string if denied.
    """
    user = get_current_user()

    if user is None:
        return json.dumps({"error": "Permission denied: no authenticated user"})

    if user.is_superuser:
        return None

    try:
        from users.permissions import check_user_role
    except ImportError:
        logger.warning("Could not import check_user_role — failing open")
        return None

    if not check_user_role(user, role, action):
        return json.dumps(
            {
                "error": f"Permission denied: user '{user.username}' lacks "
                f"'{action}' permission for role '{role}'"
            }
        )

    return None


@sync_to_async
def check_permission(role: str, action: str) -> Optional[str]:
    """Async wrapper around require_permission for use in MCP tool functions."""
    return require_permission(role, action)

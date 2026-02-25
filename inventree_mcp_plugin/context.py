"""Thread-local storage for passing request context (user) to MCP tool handlers."""

import threading

_request_context = threading.local()


def set_current_user(user):
    """Store the authenticated user for the current request thread."""
    _request_context.user = user


def get_current_user():
    """Retrieve the authenticated user for the current request thread."""
    return getattr(_request_context, "user", None)

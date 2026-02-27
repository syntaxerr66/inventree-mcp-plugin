"""Tabler icon validation using InvenTree's bundled icons.json."""

import json
import logging
import os
from functools import lru_cache

logger = logging.getLogger("inventree_mcp_plugin.tools.icons")

# Possible locations for icons.json (PKG install, source install, Docker)
_ICON_PATHS = [
    "/opt/inventree/data/static/tabler-icons/icons.json",
    "/opt/inventree/src/backend/InvenTree/InvenTree/static/tabler-icons/icons.json",
    "/home/inventree/data/static/tabler-icons/icons.json",
]


@lru_cache(maxsize=1)
def _load_icons() -> dict:
    """Load and cache the Tabler icons registry.

    Returns a dict mapping icon name -> set of valid variants.
    """
    # Try Django's static file finders first
    try:
        from django.contrib.staticfiles import finders

        path = finders.find("tabler-icons/icons.json")
        if path:
            _ICON_PATHS.insert(0, path)
    except Exception:
        pass

    for path in _ICON_PATHS:
        if os.path.isfile(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                icons = {}
                for name, info in data.items():
                    variants = info.get("variants", {})
                    if isinstance(variants, dict):
                        icons[name] = set(variants.keys())
                    else:
                        icons[name] = set()
                logger.info("Loaded %d Tabler icons from %s", len(icons), path)
                return icons
            except Exception as e:
                logger.warning("Failed to load icons from %s: %s", path, e)

    logger.warning("Could not find tabler-icons/icons.json — icon validation disabled")
    return {}


def validate_icon(icon_str: str) -> tuple[bool, str]:
    """Validate a Tabler icon string like 'ti:tool:outline'.

    Returns (is_valid, error_message). If valid, error_message is empty.
    If the icon registry couldn't be loaded, all icons are accepted.
    """
    if not icon_str or icon_str.lower() == "none":
        return True, ""

    icons = _load_icons()
    if not icons:
        # Can't validate — accept anything
        return True, ""

    parts = icon_str.split(":")
    if len(parts) != 3 or parts[0] != "ti":
        return False, f"Invalid icon format '{icon_str}'. Expected 'ti:<name>:<variant>' (e.g. 'ti:tool:outline')."

    name = parts[1]
    variant = parts[2]

    if name not in icons:
        # Find similar names for a helpful suggestion
        suggestions = [n for n in icons if name in n or n in name][:5]
        msg = f"Unknown Tabler icon '{name}'."
        if suggestions:
            formatted = ", ".join(f"ti:{s}:outline" for s in suggestions)
            msg += f" Similar: {formatted}"
        return False, msg

    if variant not in icons[name]:
        valid_variants = ", ".join(sorted(icons[name]))
        return False, f"Icon '{name}' exists but variant '{variant}' is invalid. Valid variants: {valid_variants}"

    return True, ""

"""Stock location tools — search, get, list, create, update, delete."""

import json
import logging
from typing import Optional

from ..mcp_server import mcp
from .serializers import serialize_stock_location, to_json

logger = logging.getLogger("inventree_mcp_plugin.tools.locations")


@mcp.tool()
def search_stock_locations(search: str, limit: int = 25) -> str:
    """Search for stock locations by name. Supports partial/fuzzy matching.

    Example: search for 'green' to find 'Green 1', 'Green 2', etc.
    """
    from django.db.models import Q

    from stock.models import StockLocation

    if limit <= 0:
        limit = 25

    locations = StockLocation.objects.filter(
        Q(name__icontains=search) | Q(description__icontains=search)
    )[:limit]

    results = [serialize_stock_location(loc) for loc in locations]
    return to_json({"count": len(results), "results": results})


@mcp.tool()
def get_stock_location(id: int) -> str:
    """Get detailed information about a specific stock location by its ID (pk)."""
    from stock.models import StockLocation

    try:
        location = StockLocation.objects.get(pk=id)
    except StockLocation.DoesNotExist:
        return json.dumps({"error": f"Stock location {id} not found"})

    return to_json(serialize_stock_location(location))


@mcp.tool()
def list_stock_locations(parent: int = 0, limit: int = 100, offset: int = 0) -> str:
    """List stock locations, optionally filtered by parent location.

    Set parent=0 or omit to list all locations. Use the pathstring field to understand
    the location hierarchy. Supports pagination via limit/offset.
    """
    from stock.models import StockLocation

    qs = StockLocation.objects.all()
    if parent:
        qs = qs.filter(parent_id=parent)

    total = qs.count()
    locations = qs[offset : offset + limit]
    results = [serialize_stock_location(loc) for loc in locations]

    return to_json({"count": total, "results": results})


@mcp.tool()
def create_stock_location(
    name: str,
    description: str = "",
    parent: int = 0,
    structural: Optional[bool] = None,
) -> str:
    """Create a new stock location.

    Search first to avoid duplicates. Set parent to nest under an existing location.
    Set structural=true if the location is organizational only (can't store stock directly).
    """
    from stock.models import StockLocation

    fields = {"name": name}

    if description:
        fields["description"] = description
    if parent:
        fields["parent_id"] = parent
    if structural is not None:
        fields["structural"] = structural

    location = StockLocation.objects.create(**fields)
    return to_json(serialize_stock_location(location))


@mcp.tool()
def update_stock_location(
    id: int,
    name: str = "",
    description: str = "",
    parent: int = 0,
) -> str:
    """Update an existing stock location. Only provided fields are changed."""
    from stock.models import StockLocation

    try:
        location = StockLocation.objects.get(pk=id)
    except StockLocation.DoesNotExist:
        return json.dumps({"error": f"Stock location {id} not found"})

    updated = False

    if name:
        location.name = name
        updated = True
    if description:
        location.description = description
        updated = True
    if parent:
        location.parent_id = parent
        updated = True

    if not updated:
        return json.dumps({"error": "No fields provided to update"})

    location.save()
    location.refresh_from_db()
    return to_json(serialize_stock_location(location))


@mcp.tool()
def delete_stock_location(id: int) -> str:
    """Delete a stock location. The location must be empty (no items or sub-locations)."""
    from stock.models import StockLocation

    try:
        location = StockLocation.objects.get(pk=id)
    except StockLocation.DoesNotExist:
        return f"Stock location {id} not found."

    location.delete()
    return f"Location {id} deleted successfully."

"""Stock location tools — search, get, list, create, update, delete."""

import json
import logging
from typing import Optional

from asgiref.sync import sync_to_async

from ..mcp_server import mcp
from .serializers import serialize_stock_location, to_json

logger = logging.getLogger("inventree_mcp_plugin.tools.locations")


@mcp.tool()
async def search_stock_locations(search: str, limit: int = 25) -> str:
    """Search for stock locations by name. Supports partial/fuzzy matching.

    Example: search for 'green' to find 'Green 1', 'Green 2', etc.
    """

    @sync_to_async
    def _query():
        from django.db.models import Q

        from stock.models import StockLocation

        lim = limit if limit > 0 else 25
        locations = list(
            StockLocation.objects.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )[:lim]
        )
        return [serialize_stock_location(loc) for loc in locations]

    results = await _query()
    return to_json({"count": len(results), "results": results})


@mcp.tool()
async def get_stock_location(id: int) -> str:
    """Get detailed information about a specific stock location by its ID (pk)."""

    @sync_to_async
    def _query():
        from stock.models import StockLocation

        try:
            return serialize_stock_location(StockLocation.objects.get(pk=id))
        except StockLocation.DoesNotExist:
            return {"error": f"Stock location {id} not found"}

    return to_json(await _query())


@mcp.tool()
async def list_stock_locations(parent: int = 0, limit: int = 100, offset: int = 0) -> str:
    """List stock locations, optionally filtered by parent location.

    Set parent=0 or omit to list all locations. Use the pathstring field to understand
    the location hierarchy. Supports pagination via limit/offset.
    """

    @sync_to_async
    def _query():
        from stock.models import StockLocation

        qs = StockLocation.objects.all()
        if parent:
            qs = qs.filter(parent_id=parent)
        total = qs.count()
        locations = list(qs[offset : offset + limit])
        return {"count": total, "results": [serialize_stock_location(l) for l in locations]}

    return to_json(await _query())


@mcp.tool()
async def create_stock_location(
    name: str,
    description: str = "",
    parent: int = 0,
    structural: Optional[bool] = None,
    icon: str = "",
) -> str:
    """Create a new stock location.

    Search first to avoid duplicates. Set parent to nest under an existing location.
    Set structural=true if the location is organizational only (can't store stock directly).
    Icon should be a Tabler icon string like 'ti:nail:outline' or 'ti:circle:outline'.
    """

    @sync_to_async
    def _create():
        from stock.models import StockLocation

        fields = {"name": name}
        if description:
            fields["description"] = description
        if parent:
            fields["parent_id"] = parent
        if structural is not None:
            fields["structural"] = structural
        if icon:
            fields["icon"] = icon
        location = StockLocation.objects.create(**fields)
        return serialize_stock_location(location)

    return to_json(await _create())


@mcp.tool()
async def update_stock_location(
    id: int,
    name: str = "",
    description: str = "",
    parent: int = 0,
    icon: str = "",
) -> str:
    """Update an existing stock location. Only provided fields are changed.

    Icon should be a Tabler icon string like 'ti:nail:outline' or 'ti:circle:outline'.
    Set icon to 'none' to clear an existing icon.
    """

    @sync_to_async
    def _update():
        from stock.models import StockLocation

        try:
            location = StockLocation.objects.get(pk=id)
        except StockLocation.DoesNotExist:
            return {"error": f"Stock location {id} not found"}
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
        if icon:
            location.icon = "" if icon.lower() == "none" else icon
            updated = True
        if not updated:
            return {"error": "No fields provided to update"}
        location.save()
        location.refresh_from_db()
        return serialize_stock_location(location)

    return to_json(await _update())


@mcp.tool()
async def delete_stock_location(id: int) -> str:
    """Delete a stock location. The location must be empty (no items or sub-locations)."""

    @sync_to_async
    def _delete():
        from stock.models import StockLocation

        try:
            location = StockLocation.objects.get(pk=id)
        except StockLocation.DoesNotExist:
            return f"Stock location {id} not found."
        location.delete()
        return f"Location {id} deleted successfully."

    return await _delete()

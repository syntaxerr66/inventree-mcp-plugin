"""Stock location tools — search, get, list, create, update, delete."""

import json
import logging
from typing import Optional

from asgiref.sync import sync_to_async

from ..mcp_server import mcp
from .icons import validate_icon
from .serializers import serialize_stock_location, serialize_stock_location_compact, to_json

logger = logging.getLogger("inventree_mcp_plugin.tools.locations")


@mcp.tool()
async def search_stock_locations(search: str = "", parent: int = 0, limit: int = 10, offset: int = 0) -> str:
    """Search and list stock locations. Returns compact results; use get_stock_location(id) for full detail.

    Combine filters: search by name AND/OR filter by parent location.
    Set search="" and parent=0 to list all locations.
    Default limit is 10 — check the count field for total matches and
    increase limit or paginate with offset if needed.
    """
    from ..permissions import check_permission
    if perm_err := await check_permission('stock_location', 'view'):
        return perm_err

    @sync_to_async
    def _query():
        from stock.models import StockLocation

        qs = StockLocation.objects.all()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        if parent:
            qs = qs.filter(parent_id=parent)
        lim = limit if limit > 0 else 10
        total = qs.count()
        locations = list(qs[offset : offset + lim])
        return {"count": total, "results": [serialize_stock_location_compact(loc) for loc in locations]}

    return to_json(await _query())


@mcp.tool()
async def get_stock_location(id: int) -> str:
    """Get detailed information about a specific stock location by its ID (pk)."""
    from ..permissions import check_permission
    if perm_err := await check_permission('stock_location', 'view'):
        return perm_err

    @sync_to_async
    def _query():
        from stock.models import StockLocation

        try:
            return serialize_stock_location(StockLocation.objects.get(pk=id))
        except StockLocation.DoesNotExist:
            return {"error": f"Stock location {id} not found"}

    return to_json(await _query())


@mcp.tool()
async def create_stock_location(
    name: str,
    description: str = "",
    parent: int = 0,
    structural: Optional[bool] = None,
    icon: str = "",
    location_type: int = 0,
) -> str:
    """Create a new stock location.

    Search first to avoid duplicates. Set parent to nest under an existing location.
    Set structural=true if the location is organizational only (can't store stock directly).
    Icon should be a Tabler icon string like 'ti:tool:outline' or 'ti:circle:outline'.
    Set location_type to a StockLocationType ID to classify this location (use list_location_types).
    """
    from ..permissions import check_permission
    if perm_err := await check_permission('stock_location', 'add'):
        return perm_err

    if icon:
        valid, err = validate_icon(icon)
        if not valid:
            return to_json({"error": err})

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
        if location_type:
            fields["location_type_id"] = location_type
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
    location_type: int = 0,
) -> str:
    """Update an existing stock location. Only provided fields are changed.

    Icon should be a Tabler icon string like 'ti:tool:outline' or 'ti:circle:outline'.
    Set icon to 'none' to clear an existing icon.
    Set location_type to a StockLocationType ID to classify this location.
    Set location_type to -1 to clear the location type.
    """
    from ..permissions import check_permission
    if perm_err := await check_permission('stock_location', 'change'):
        return perm_err

    if icon and icon.lower() != "none":
        valid, err = validate_icon(icon)
        if not valid:
            return to_json({"error": err})

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
        if location_type == -1:
            location.location_type = None
            updated = True
        elif location_type:
            location.location_type_id = location_type
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
    from ..permissions import check_permission
    if perm_err := await check_permission('stock_location', 'delete'):
        return perm_err

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

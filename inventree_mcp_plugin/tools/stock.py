"""Stock tools — get, get_item, add, add_qty, remove_qty, transfer, delete."""

import json
import logging
from typing import Optional

from asgiref.sync import sync_to_async

from ..mcp_server import mcp
from .serializers import serialize_stock_item, to_json

logger = logging.getLogger("inventree_mcp_plugin.tools.stock")


@mcp.tool()
async def get_stock(
    part: int = 0,
    location: int = 0,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """List stock items, optionally filtered by part ID and/or location ID.

    Set part=0 and location=0 to list all stock. Supports pagination via limit/offset.
    """

    @sync_to_async
    def _query():
        from stock.models import StockItem

        qs = StockItem.objects.all()
        if part:
            qs = qs.filter(part_id=part)
        if location:
            qs = qs.filter(location_id=location)
        total = qs.count()
        items = list(qs.select_related("part")[offset : offset + limit])
        return {"count": total, "results": [serialize_stock_item(i) for i in items]}

    return to_json(await _query())


@mcp.tool()
async def get_stock_item(id: int) -> str:
    """Get detailed information about a specific stock item by its ID (pk)."""

    @sync_to_async
    def _query():
        from stock.models import StockItem

        try:
            item = StockItem.objects.select_related("part").get(pk=id)
            return serialize_stock_item(item)
        except StockItem.DoesNotExist:
            return {"error": f"Stock item {id} not found"}

    return to_json(await _query())


@mcp.tool()
async def add_stock(
    part: int,
    quantity: float,
    location: int = 0,
    batch: str = "",
    serial: str = "",
    notes: str = "",
) -> str:
    """Create a new stock item for a part.

    For trackable parts, provide a serial number. Set location=0 to leave unassigned.
    """

    @sync_to_async
    def _create():
        from stock.models import StockItem

        from ..context import get_current_user

        fields = {"part_id": part, "quantity": quantity}
        if location:
            fields["location_id"] = location
        if batch:
            fields["batch"] = batch
        if serial:
            fields["serial"] = serial
        if notes:
            fields["notes"] = notes

        user = get_current_user()
        item = StockItem(**fields)
        item.save(user=user)
        return serialize_stock_item(item)

    return to_json(await _create())


@mcp.tool()
async def stock_add_quantity(items: list, notes: str = "") -> str:
    """Add quantity to existing stock items. Increases stock levels without creating new entries.

    items: list of objects, each with 'pk' (stock item ID) and 'quantity' (amount to add).
    Example: [{"pk": 1, "quantity": 10}, {"pk": 2, "quantity": 5}]
    """

    @sync_to_async
    def _add():
        from stock.models import StockItem

        from ..context import get_current_user

        user = get_current_user()
        for adj in items:
            pk = adj.get("pk") or adj.get("id")
            qty = adj.get("quantity", 0)
            if not pk or not qty:
                continue
            try:
                stock_item = StockItem.objects.get(pk=pk)
                stock_item.add_stock(qty, user, notes=notes)
            except StockItem.DoesNotExist:
                return {"error": f"Stock item {pk} not found"}
            except Exception as e:
                return {"error": f"Failed to add stock to item {pk}: {e}"}
        return None

    err = await _add()
    if err:
        return to_json(err)
    return "Stock quantity updated successfully."


@mcp.tool()
async def stock_remove_quantity(items: list, notes: str = "") -> str:
    """Remove quantity from existing stock items. Decreases stock levels.

    items: list of objects, each with 'pk' (stock item ID) and 'quantity' (amount to remove).
    Example: [{"pk": 1, "quantity": 5}]
    """

    @sync_to_async
    def _remove():
        from stock.models import StockItem

        from ..context import get_current_user

        user = get_current_user()
        for adj in items:
            pk = adj.get("pk") or adj.get("id")
            qty = adj.get("quantity", 0)
            if not pk or not qty:
                continue
            try:
                stock_item = StockItem.objects.get(pk=pk)
                stock_item.take_stock(qty, user, notes=notes)
            except StockItem.DoesNotExist:
                return {"error": f"Stock item {pk} not found"}
            except Exception as e:
                return {"error": f"Failed to remove stock from item {pk}: {e}"}
        return None

    err = await _remove()
    if err:
        return to_json(err)
    return "Stock quantity removed successfully."


@mcp.tool()
async def stock_transfer(items: list, location: int, notes: str = "") -> str:
    """Transfer stock items to a different location.

    items: list of objects, each with 'pk' (stock item ID) and 'quantity' (amount to transfer).
    location: destination stock location ID.
    Example: stock_transfer(items=[{"pk": 1, "quantity": 5}], location=3)
    """

    @sync_to_async
    def _transfer():
        from stock.models import StockItem, StockLocation

        from ..context import get_current_user

        user = get_current_user()
        try:
            dest = StockLocation.objects.get(pk=location)
        except StockLocation.DoesNotExist:
            return {"error": f"Location {location} not found"}
        for adj in items:
            pk = adj.get("pk") or adj.get("id")
            if not pk:
                continue
            try:
                stock_item = StockItem.objects.get(pk=pk)
                stock_item.move(dest, notes, user)
            except StockItem.DoesNotExist:
                return {"error": f"Stock item {pk} not found"}
            except Exception as e:
                return {"error": f"Failed to transfer stock item {pk}: {e}"}
        return None

    err = await _transfer()
    if err:
        return to_json(err)
    return "Stock transferred successfully."


@mcp.tool()
async def delete_stock_item(id: int) -> str:
    """Delete a stock item permanently."""

    @sync_to_async
    def _delete():
        from stock.models import StockItem

        try:
            item = StockItem.objects.get(pk=id)
        except StockItem.DoesNotExist:
            return f"Stock item {id} not found."
        item.delete()
        return f"Stock item {id} deleted successfully."

    return await _delete()

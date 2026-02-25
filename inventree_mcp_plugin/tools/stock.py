"""Stock tools — get, get_item, add, add_qty, remove_qty, transfer, delete."""

import json
import logging
from typing import Optional

from ..mcp_server import mcp
from .serializers import serialize_stock_item, to_json

logger = logging.getLogger("inventree_mcp_plugin.tools.stock")


@mcp.tool()
def get_stock(
    part: int = 0,
    location: int = 0,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """List stock items, optionally filtered by part ID and/or location ID.

    Set part=0 and location=0 to list all stock. Supports pagination via limit/offset.
    """
    from stock.models import StockItem

    qs = StockItem.objects.all()
    if part:
        qs = qs.filter(part_id=part)
    if location:
        qs = qs.filter(location_id=location)

    total = qs.count()
    items = qs.select_related("part")[offset : offset + limit]
    results = [serialize_stock_item(item) for item in items]

    return to_json({"count": total, "results": results})


@mcp.tool()
def get_stock_item(id: int) -> str:
    """Get detailed information about a specific stock item by its ID (pk)."""
    from stock.models import StockItem

    try:
        item = StockItem.objects.select_related("part").get(pk=id)
    except StockItem.DoesNotExist:
        return json.dumps({"error": f"Stock item {id} not found"})

    return to_json(serialize_stock_item(item))


@mcp.tool()
def add_stock(
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
    from stock.models import StockItem

    from ..context import get_current_user

    fields = {
        "part_id": part,
        "quantity": quantity,
    }

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

    return to_json(serialize_stock_item(item))


@mcp.tool()
def stock_add_quantity(items: list, notes: str = "") -> str:
    """Add quantity to existing stock items. Increases stock levels without creating new entries.

    items: list of objects, each with 'pk' (stock item ID) and 'quantity' (amount to add).
    Example: [{"pk": 1, "quantity": 10}, {"pk": 2, "quantity": 5}]
    """
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
            return json.dumps({"error": f"Stock item {pk} not found"})
        except Exception as e:
            return json.dumps({"error": f"Failed to add stock to item {pk}: {e}"})

    return "Stock quantity updated successfully."


@mcp.tool()
def stock_remove_quantity(items: list, notes: str = "") -> str:
    """Remove quantity from existing stock items. Decreases stock levels.

    items: list of objects, each with 'pk' (stock item ID) and 'quantity' (amount to remove).
    Example: [{"pk": 1, "quantity": 5}]
    """
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
            return json.dumps({"error": f"Stock item {pk} not found"})
        except Exception as e:
            return json.dumps({"error": f"Failed to remove stock from item {pk}: {e}"})

    return "Stock quantity removed successfully."


@mcp.tool()
def stock_transfer(items: list, location: int, notes: str = "") -> str:
    """Transfer stock items to a different location.

    items: list of objects, each with 'pk' (stock item ID) and 'quantity' (amount to transfer).
    location: destination stock location ID.
    Example: stock_transfer(items=[{"pk": 1, "quantity": 5}], location=3)
    """
    from stock.models import StockItem, StockLocation

    from ..context import get_current_user

    user = get_current_user()

    try:
        dest = StockLocation.objects.get(pk=location)
    except StockLocation.DoesNotExist:
        return json.dumps({"error": f"Location {location} not found"})

    for adj in items:
        pk = adj.get("pk") or adj.get("id")
        if not pk:
            continue

        try:
            stock_item = StockItem.objects.get(pk=pk)
            stock_item.move(dest, notes, user)
        except StockItem.DoesNotExist:
            return json.dumps({"error": f"Stock item {pk} not found"})
        except Exception as e:
            return json.dumps({"error": f"Failed to transfer stock item {pk}: {e}"})

    return "Stock transferred successfully."


@mcp.tool()
def delete_stock_item(id: int) -> str:
    """Delete a stock item permanently."""
    from stock.models import StockItem

    try:
        item = StockItem.objects.get(pk=id)
    except StockItem.DoesNotExist:
        return f"Stock item {id} not found."

    item.delete()
    return f"Stock item {id} deleted successfully."

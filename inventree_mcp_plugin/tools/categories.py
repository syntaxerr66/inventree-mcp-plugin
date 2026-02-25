"""Part category tools — search, list, create, update, delete."""

import json
import logging
from typing import Optional

from asgiref.sync import sync_to_async

from ..mcp_server import mcp
from .serializers import serialize_part_category, to_json

logger = logging.getLogger("inventree_mcp_plugin.tools.categories")


@mcp.tool()
async def search_part_categories(search: str, limit: int = 25) -> str:
    """Search for part categories by name.

    Use the pathstring field to understand the full category hierarchy.
    """

    @sync_to_async
    def _query():
        from django.db.models import Q

        from part.models import PartCategory

        lim = limit if limit > 0 else 25
        categories = list(
            PartCategory.objects.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )[:lim]
        )
        return [serialize_part_category(cat) for cat in categories]

    results = await _query()
    return to_json({"count": len(results), "results": results})


@mcp.tool()
async def list_part_categories(parent: int = 0, limit: int = 100, offset: int = 0) -> str:
    """List part categories, optionally filtered by parent.

    Set parent=0 or omit to list all categories. The pathstring field shows the full
    hierarchy path (e.g. 'Electronic Components/Resistors/Through Hole').
    Supports pagination via limit/offset.
    """

    @sync_to_async
    def _query():
        from part.models import PartCategory

        qs = PartCategory.objects.all()
        if parent:
            qs = qs.filter(parent_id=parent)
        total = qs.count()
        categories = list(qs[offset : offset + limit])
        return {"count": total, "results": [serialize_part_category(c) for c in categories]}

    return to_json(await _query())


@mcp.tool()
async def create_part_category(
    name: str,
    description: str = "",
    parent: int = 0,
    default_location: int = 0,
    structural: Optional[bool] = None,
) -> str:
    """Create a new part category.

    Always search for existing categories first to avoid duplicates.
    Categories can be deeply nested; set parent to the parent category ID.
    """

    @sync_to_async
    def _create():
        from part.models import PartCategory

        fields = {"name": name}
        if description:
            fields["description"] = description
        if parent:
            fields["parent_id"] = parent
        if default_location:
            fields["default_location_id"] = default_location
        if structural is not None:
            fields["structural"] = structural
        category = PartCategory.objects.create(**fields)
        return serialize_part_category(category)

    return to_json(await _create())


@mcp.tool()
async def update_part_category(
    id: int,
    name: str = "",
    description: str = "",
    parent: int = 0,
    default_location: int = 0,
) -> str:
    """Update an existing part category. Only provided fields are changed."""

    @sync_to_async
    def _update():
        from part.models import PartCategory

        try:
            category = PartCategory.objects.get(pk=id)
        except PartCategory.DoesNotExist:
            return {"error": f"Part category {id} not found"}
        updated = False
        if name:
            category.name = name
            updated = True
        if description:
            category.description = description
            updated = True
        if parent:
            category.parent_id = parent
            updated = True
        if default_location:
            category.default_location_id = default_location
            updated = True
        if not updated:
            return {"error": "No fields provided to update"}
        category.save()
        category.refresh_from_db()
        return serialize_part_category(category)

    return to_json(await _update())


@mcp.tool()
async def delete_part_category(id: int) -> str:
    """Delete a part category. Must have no parts or sub-categories."""

    @sync_to_async
    def _delete():
        from part.models import PartCategory

        try:
            category = PartCategory.objects.get(pk=id)
        except PartCategory.DoesNotExist:
            return f"Part category {id} not found."
        category.delete()
        return f"Category {id} deleted successfully."

    return await _delete()

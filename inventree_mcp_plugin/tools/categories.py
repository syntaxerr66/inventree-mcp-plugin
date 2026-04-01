"""Part category tools — search, list, create, update, delete."""

import json
import logging
from typing import Optional

from asgiref.sync import sync_to_async

from ..mcp_server import mcp
from .icons import validate_icon
from .serializers import serialize_part_category, serialize_part_category_compact, to_json

logger = logging.getLogger("inventree_mcp_plugin.tools.categories")


@mcp.tool()
async def search_part_categories(search: str = "", parent: int = 0, limit: int = 10, offset: int = 0) -> str:
    """Search and list part categories. Returns compact results; use pathstring for hierarchy.

    Combine filters: search by name AND/OR filter by parent category.
    Set search="" and parent=0 to list all categories.
    Default limit is 10 — check the count field for total matches and
    increase limit or paginate with offset if needed.
    """
    from ..permissions import check_permission
    if perm_err := await check_permission('part_category', 'view'):
        return perm_err

    @sync_to_async
    def _query():
        from part.models import PartCategory

        qs = PartCategory.objects.all()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        if parent:
            qs = qs.filter(parent_id=parent)
        lim = limit if limit > 0 else 10
        total = qs.count()
        categories = list(qs[offset : offset + lim])
        return {"count": total, "results": [serialize_part_category_compact(c) for c in categories]}

    return to_json(await _query())


@mcp.tool()
async def create_part_category(
    name: str,
    description: str = "",
    parent: int = 0,
    default_location: int = 0,
    structural: Optional[bool] = None,
    icon: str = "",
) -> str:
    """Create a new part category.

    Always search for existing categories first to avoid duplicates.
    Categories can be deeply nested; set parent to the parent category ID.
    Icon should be a Tabler icon string like 'ti:tool:outline' or 'ti:circle:outline'.
    """
    from ..permissions import check_permission
    if perm_err := await check_permission('part_category', 'add'):
        return perm_err

    if icon:
        valid, err = validate_icon(icon)
        if not valid:
            return to_json({"error": err})

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
        if icon:
            fields["icon"] = icon
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
    icon: str = "",
) -> str:
    """Update an existing part category. Only provided fields are changed.

    Icon should be a Tabler icon string like 'ti:tool:outline' or 'ti:circle:outline'.
    Set icon to 'none' to clear an existing icon.
    """
    from ..permissions import check_permission
    if perm_err := await check_permission('part_category', 'change'):
        return perm_err

    if icon and icon.lower() != "none":
        valid, err = validate_icon(icon)
        if not valid:
            return to_json({"error": err})

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
        if icon:
            category.icon = "" if icon.lower() == "none" else icon
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
    from ..permissions import check_permission
    if perm_err := await check_permission('part_category', 'delete'):
        return perm_err

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

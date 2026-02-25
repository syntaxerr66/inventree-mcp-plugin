"""Part category tools — search, list, create, update, delete."""

import json
import logging
from typing import Optional

from ..mcp_server import mcp
from .serializers import serialize_part_category, to_json

logger = logging.getLogger("inventree_mcp_plugin.tools.categories")


@mcp.tool()
def search_part_categories(search: str, limit: int = 25) -> str:
    """Search for part categories by name.

    Use the pathstring field to understand the full category hierarchy.
    """
    from django.db.models import Q

    from part.models import PartCategory

    if limit <= 0:
        limit = 25

    categories = PartCategory.objects.filter(
        Q(name__icontains=search) | Q(description__icontains=search)
    )[:limit]

    results = [serialize_part_category(cat) for cat in categories]
    return to_json({"count": len(results), "results": results})


@mcp.tool()
def list_part_categories(parent: int = 0, limit: int = 100, offset: int = 0) -> str:
    """List part categories, optionally filtered by parent.

    Set parent=0 or omit to list all categories. The pathstring field shows the full
    hierarchy path (e.g. 'Electronic Components/Resistors/Through Hole').
    Supports pagination via limit/offset.
    """
    from part.models import PartCategory

    qs = PartCategory.objects.all()
    if parent:
        qs = qs.filter(parent_id=parent)

    total = qs.count()
    categories = qs[offset : offset + limit]
    results = [serialize_part_category(cat) for cat in categories]

    return to_json({"count": total, "results": results})


@mcp.tool()
def create_part_category(
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
    return to_json(serialize_part_category(category))


@mcp.tool()
def update_part_category(
    id: int,
    name: str = "",
    description: str = "",
    parent: int = 0,
    default_location: int = 0,
) -> str:
    """Update an existing part category. Only provided fields are changed."""
    from part.models import PartCategory

    try:
        category = PartCategory.objects.get(pk=id)
    except PartCategory.DoesNotExist:
        return json.dumps({"error": f"Part category {id} not found"})

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
        return json.dumps({"error": "No fields provided to update"})

    category.save()
    category.refresh_from_db()
    return to_json(serialize_part_category(category))


@mcp.tool()
def delete_part_category(id: int) -> str:
    """Delete a part category. Must have no parts or sub-categories."""
    from part.models import PartCategory

    try:
        category = PartCategory.objects.get(pk=id)
    except PartCategory.DoesNotExist:
        return f"Part category {id} not found."

    category.delete()
    return f"Category {id} deleted successfully."

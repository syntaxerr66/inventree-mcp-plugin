"""Part tools — search, get, create, update, delete, list, set_image, search_images."""

import json
import logging
from typing import Optional

from ..mcp_server import mcp
from .serializers import serialize_part, to_json

logger = logging.getLogger("inventree_mcp_plugin.tools.parts")


@mcp.tool()
def search_parts(search: str, limit: int = 25) -> str:
    """Search for parts by keyword. Returns matching parts with details.

    Searches across part name, description, IPN, and keywords.
    """
    from django.db.models import Q

    from part.models import Part

    if limit <= 0:
        limit = 25

    parts = Part.objects.filter(
        Q(name__icontains=search)
        | Q(description__icontains=search)
        | Q(IPN__icontains=search)
        | Q(keywords__icontains=search)
    )[:limit]

    results = [serialize_part(p) for p in parts]
    return to_json({"count": len(results), "results": results})


@mcp.tool()
def get_part(id: int) -> str:
    """Get detailed information about a specific part by its ID (pk)."""
    from part.models import Part

    try:
        part = Part.objects.get(pk=id)
    except Part.DoesNotExist:
        return json.dumps({"error": f"Part {id} not found"})

    return to_json(serialize_part(part))


@mcp.tool()
def create_part(
    name: str,
    description: str = "",
    category: int = 0,
    IPN: str = "",
    keywords: str = "",
    units: str = "",
    minimum_stock: int = 0,
    purchaseable: Optional[bool] = None,
    component: Optional[bool] = None,
    assembly: Optional[bool] = None,
    trackable: Optional[bool] = None,
    virtual: Optional[bool] = None,
    image_url: str = "",
) -> str:
    """Create a new part.

    Always use this workflow: search_parts first to check for duplicates,
    then list_part_categories (check pathstring fields for nesting) to find
    the deepest matching category, then create the part with the correct category ID.

    Set category=0 or omit for uncategorized. image_url is a URL that InvenTree
    will download the image from server-side.
    """
    from part.models import Part

    fields = {"name": name}

    if description:
        fields["description"] = description
    if category:
        fields["category_id"] = category
    if IPN:
        fields["IPN"] = IPN
    if keywords:
        fields["keywords"] = keywords
    if units:
        fields["units"] = units
    if minimum_stock:
        fields["minimum_stock"] = minimum_stock
    if purchaseable is not None:
        fields["purchaseable"] = purchaseable
    if component is not None:
        fields["component"] = component
    if assembly is not None:
        fields["assembly"] = assembly
    if trackable is not None:
        fields["trackable"] = trackable
    if virtual is not None:
        fields["virtual"] = virtual

    part = Part.objects.create(**fields)

    # Handle remote image download
    if image_url:
        try:
            part.remote_image = image_url
            part.save()
        except Exception as e:
            logger.warning(f"Failed to set image for part {part.pk}: {e}")

    return to_json(serialize_part(part))


@mcp.tool()
def update_part(
    id: int,
    name: str = "",
    description: str = "",
    category: int = 0,
    active: Optional[bool] = None,
    IPN: str = "",
    keywords: str = "",
    units: str = "",
    minimum_stock: int = 0,
    image_url: str = "",
) -> str:
    """Update an existing part. Only provided fields are changed.

    Set image_url to a URL and InvenTree will download the image server-side.
    """
    from part.models import Part

    try:
        part = Part.objects.get(pk=id)
    except Part.DoesNotExist:
        return json.dumps({"error": f"Part {id} not found"})

    updated = False

    if name:
        part.name = name
        updated = True
    if description:
        part.description = description
        updated = True
    if category:
        part.category_id = category
        updated = True
    if active is not None:
        part.active = active
        updated = True
    if IPN:
        part.IPN = IPN
        updated = True
    if keywords:
        part.keywords = keywords
        updated = True
    if units:
        part.units = units
        updated = True
    if minimum_stock:
        part.minimum_stock = minimum_stock
        updated = True

    if not updated and not image_url:
        return json.dumps({"error": "No fields provided to update"})

    if updated:
        part.save()

    if image_url:
        try:
            part.remote_image = image_url
            part.save()
        except Exception as e:
            logger.warning(f"Failed to set image for part {part.pk}: {e}")

    part.refresh_from_db()
    return to_json(serialize_part(part))


@mcp.tool()
def delete_part(id: int) -> str:
    """Delete a part. The part is first deactivated, then deleted.

    The part must have no stock items before it can be deleted.
    """
    from part.models import Part

    try:
        part = Part.objects.get(pk=id)
    except Part.DoesNotExist:
        return f"Part {id} not found."

    # Deactivate first (InvenTree requires this)
    part.active = False
    part.save()

    part.delete()
    return f"Part {id} deleted successfully."


@mcp.tool()
def list_parts(category: int = 0, limit: int = 50, offset: int = 0) -> str:
    """List parts, optionally filtered by category.

    Set category=0 or omit to list all parts. Supports pagination via limit/offset.
    """
    from part.models import Part

    qs = Part.objects.all()
    if category:
        qs = qs.filter(category_id=category)

    total = qs.count()
    parts = qs[offset : offset + limit]
    results = [serialize_part(p) for p in parts]

    return to_json({"count": total, "results": results})


@mcp.tool()
def set_part_image(id: int, image_url: str) -> str:
    """Set a part's image by URL. InvenTree downloads the image server-side.

    Use search_part_images to find image URLs, then pass one here.
    """
    from part.models import Part

    try:
        part = Part.objects.get(pk=id)
    except Part.DoesNotExist:
        return json.dumps({"error": f"Part {id} not found"})

    try:
        part.remote_image = image_url
        part.save()
    except Exception as e:
        return json.dumps({"error": f"Failed to set image: {e}"})

    part.refresh_from_db()
    return to_json(serialize_part(part))


@mcp.tool()
def search_part_images(query: str, num: int = 5) -> str:
    """Search Google Images for part photos. Requires GOOGLE_API_KEY and GOOGLE_CSE_ID plugin settings.

    Returns image URLs that can be passed to set_part_image or create_part(image_url=...).
    Tip: include manufacturer name or 'datasheet' in query for better results.
    """
    import requests

    from plugin.registry import registry

    # Clamp num to 1-10
    num = max(1, min(10, num))

    # Get API credentials from plugin settings
    plugin = registry.get_plugin("inventree-mcp")
    if plugin is None:
        return json.dumps({"error": "Plugin not found in registry"})

    api_key = plugin.get_setting("GOOGLE_API_KEY")
    cse_id = plugin.get_setting("GOOGLE_CSE_ID")

    if not api_key or not cse_id:
        return json.dumps(
            {
                "error": "Image search is not configured. Set GOOGLE_API_KEY and GOOGLE_CSE_ID in plugin settings."
            }
        )

    try:
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": api_key,
                "cx": cse_id,
                "q": query,
                "searchType": "image",
                "num": num,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return json.dumps({"error": f"Image search failed: {e}"})

    results = []
    for item in data.get("items", []):
        img = item.get("image", {})
        results.append(
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "thumbnail_url": img.get("thumbnailLink", ""),
                "context_url": img.get("contextLink", ""),
                "width": img.get("width", 0),
                "height": img.get("height", 0),
            }
        )

    return to_json({"query": query, "count": len(results), "results": results})

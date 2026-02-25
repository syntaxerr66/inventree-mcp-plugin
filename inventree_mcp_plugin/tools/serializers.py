"""Serialization helpers for converting InvenTree ORM objects to dicts.

Output format matches the Go MCP server for client compatibility.
"""

import json


def serialize_part(part):
    """Serialize a Part model instance to a dict."""
    data = {
        "pk": part.pk,
        "name": part.name,
        "description": part.description or "",
        "category": part.category_id,
        "IPN": part.IPN or "",
        "keywords": part.keywords or "",
        "units": part.units or "",
        "minimum_stock": float(part.minimum_stock) if part.minimum_stock else 0,
        "purchaseable": part.purchaseable,
        "component": part.component,
        "assembly": part.assembly,
        "trackable": part.trackable,
        "virtual": part.virtual,
        "active": part.active,
    }

    # Image fields
    if part.image:
        try:
            data["image"] = part.image.url
        except Exception:
            data["image"] = None
    else:
        data["image"] = None

    data["thumbnail"] = data["image"]  # Simplified; InvenTree generates thumbnails separately

    return data


def serialize_stock_item(item):
    """Serialize a StockItem model instance to a dict."""
    data = {
        "pk": item.pk,
        "part": item.part_id,
        "quantity": float(item.quantity),
        "serial": getattr(item, "serial", None) or "",
        "batch": item.batch or "",
        "location": item.location_id,
        "in_stock": bool(item.in_stock) if hasattr(item, "in_stock") else True,
        "status": item.status,
        "notes": item.notes or "",
    }

    # Timestamp
    if hasattr(item, "updated") and item.updated:
        data["updated"] = item.updated.isoformat()
    else:
        data["updated"] = ""

    # Status text
    try:
        data["status_text"] = str(item.status_label) if hasattr(item, "status_label") else ""
    except Exception:
        data["status_text"] = ""

    # Part detail (nested)
    try:
        data["part_detail"] = {
            "pk": item.part.pk,
            "name": item.part.name,
            "full_name": item.part.full_name if hasattr(item.part, "full_name") else item.part.name,
        }
    except Exception:
        data["part_detail"] = None

    return data


def serialize_stock_location(location):
    """Serialize a StockLocation model instance to a dict."""
    data = {
        "pk": location.pk,
        "name": location.name,
        "description": location.description or "",
        "parent": location.parent_id,
        "pathstring": location.pathstring if hasattr(location, "pathstring") else location.name,
        "level": location.level if hasattr(location, "level") else 0,
        "structural": getattr(location, "structural", False),
        "external": getattr(location, "external", False),
        "icon": getattr(location, "icon", "") or "",
    }

    # Count items and sublocations
    try:
        data["items"] = location.stock_items.count() if hasattr(location, "stock_items") else 0
    except Exception:
        data["items"] = 0

    try:
        data["sublocations"] = location.children.count() if hasattr(location, "children") else 0
    except Exception:
        data["sublocations"] = 0

    return data


def serialize_part_category(category):
    """Serialize a PartCategory model instance to a dict."""
    data = {
        "pk": category.pk,
        "name": category.name,
        "description": category.description or "",
        "parent": category.parent_id,
        "pathstring": category.pathstring if hasattr(category, "pathstring") else category.name,
        "level": category.level if hasattr(category, "level") else 0,
        "structural": getattr(category, "structural", False),
        "starred": getattr(category, "starred", False),
        "icon": getattr(category, "icon", "") or "",
        "default_location": getattr(category, "default_location_id", None),
    }

    # Counts
    try:
        data["part_count"] = category.parts.count() if hasattr(category, "parts") else 0
    except Exception:
        data["part_count"] = 0

    try:
        data["subcategories"] = category.children.count() if hasattr(category, "children") else 0
    except Exception:
        data["subcategories"] = 0

    return data


def to_json(data, indent=2):
    """Serialize data to indented JSON string."""
    return json.dumps(data, indent=indent, default=str)

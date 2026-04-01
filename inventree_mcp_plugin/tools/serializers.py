"""Serialization helpers for converting InvenTree ORM objects to dicts.

Output format matches the Go MCP server for client compatibility.
"""

import json


def serialize_part(part):
    """Serialize a Part model instance to a dict (full detail)."""
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

    # Image field
    if part.image:
        try:
            data["image"] = part.image.url
        except Exception:
            data["image"] = None
    else:
        data["image"] = None

    return data


def serialize_part_compact(part):
    """Compact part serialization for list/search results."""
    return {
        "pk": part.pk,
        "name": part.name,
        "description": part.description or "",
        "category": part.category_id,
    }


def serialize_stock_item(item):
    """Serialize a StockItem model instance to a dict (full detail)."""
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


def serialize_stock_item_compact(item):
    """Compact stock item serialization for list results."""
    return {
        "pk": item.pk,
        "part": item.part_id,
        "quantity": float(item.quantity),
        "location": item.location_id,
        "part_name": item.part.name if hasattr(item, "part") and item.part else "",
    }


def serialize_stock_location(location):
    """Serialize a StockLocation model instance to a dict (full detail)."""
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

    # Location type (nullable FK)
    loc_type = getattr(location, "location_type", None)
    if loc_type:
        data["location_type"] = {"pk": loc_type.pk, "name": loc_type.name}
    else:
        data["location_type"] = None

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


def serialize_stock_location_compact(location):
    """Compact location serialization for list/search results."""
    data = {
        "pk": location.pk,
        "name": location.name,
        "pathstring": location.pathstring if hasattr(location, "pathstring") else location.name,
        "parent": location.parent_id,
    }
    loc_type = getattr(location, "location_type", None)
    if loc_type:
        data["location_type"] = loc_type.name
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
    """Serialize a PartCategory model instance to a dict (full detail)."""
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


def serialize_part_category_compact(category):
    """Compact category serialization for list/search results."""
    data = {
        "pk": category.pk,
        "name": category.name,
        "pathstring": category.pathstring if hasattr(category, "pathstring") else category.name,
        "parent": category.parent_id,
    }
    try:
        data["part_count"] = category.parts.count() if hasattr(category, "parts") else 0
    except Exception:
        data["part_count"] = 0
    try:
        data["subcategories"] = category.children.count() if hasattr(category, "children") else 0
    except Exception:
        data["subcategories"] = 0
    return data


def serialize_parameter_template(tmpl):
    """Serialize a PartParameterTemplate (part.models) to a dict."""
    return {
        "pk": tmpl.pk,
        "name": tmpl.name,
        "units": tmpl.units or "",
        "description": getattr(tmpl, "description", "") or "",
        "choices": getattr(tmpl, "choices", "") or "",
        "checkbox": getattr(tmpl, "checkbox", False),
    }


def serialize_part_parameter(param):
    """Serialize a PartParameter (part.models) to a dict."""
    data = {
        "pk": param.pk,
        "template": {
            "pk": param.template.pk,
            "name": param.template.name,
            "units": param.template.units or "",
        },
        "data": param.data or "",
        "data_numeric": float(param.data_numeric) if param.data_numeric is not None else None,
    }
    if hasattr(param, "note"):
        data["note"] = param.note or ""
    if hasattr(param, "updated") and param.updated:
        data["updated"] = param.updated.isoformat()
    return data


def serialize_category_parameter(cat_param):
    """Serialize a PartCategoryParameterTemplate to a dict."""
    return {
        "pk": cat_param.pk,
        "category": cat_param.category_id,
        "template": {
            "pk": cat_param.parameter_template.pk,
            "name": cat_param.parameter_template.name,
            "units": cat_param.parameter_template.units or "",
        },
        "default_value": cat_param.default_value or "",
    }


def serialize_location_type(loc_type):
    """Serialize a StockLocationType to a dict."""
    data = {
        "pk": loc_type.pk,
        "name": loc_type.name,
        "description": getattr(loc_type, "description", "") or "",
        "icon": getattr(loc_type, "icon", "") or "",
    }
    try:
        data["location_count"] = loc_type.stock_locations.count()
    except Exception:
        data["location_count"] = 0
    return data


def to_json(data):
    """Serialize data to compact JSON string."""
    return json.dumps(data, separators=(",", ":"), default=str)

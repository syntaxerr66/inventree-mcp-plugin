"""Parameter tools — templates, part parameters, category parameters, location types."""

import logging

from asgiref.sync import sync_to_async

from ..mcp_server import mcp
from .icons import validate_icon
from .serializers import (
    serialize_category_parameter,
    serialize_location_type,
    serialize_parameter_template,
    serialize_part_parameter,
    to_json,
)

logger = logging.getLogger("inventree_mcp_plugin.tools.parameters")


# ---------------------------------------------------------------------------
# Parameter Templates
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_parameter_templates(search: str = "", limit: int = 50) -> str:
    """List or search parameter templates (the definitions, not values).

    These templates define what parameters exist (e.g. 'Thread Size', 'Material').
    Set search="" to list all templates.
    """

    @sync_to_async
    def _query():
        from part.models import PartParameterTemplate

        qs = PartParameterTemplate.objects.all()
        if search:
            from django.db.models import Q

            qs = qs.filter(
                Q(name__icontains=search)
                | Q(units__icontains=search)
                | Q(description__icontains=search)
            )
        lim = limit if limit > 0 else 50
        templates = list(qs.order_by("name")[:lim])
        return [serialize_parameter_template(t) for t in templates]

    results = await _query()
    return to_json({"count": len(results), "results": results})


@mcp.tool()
async def create_parameter_template(
    name: str,
    units: str = "",
    description: str = "",
    choices: str = "",
    checkbox: bool = False,
) -> str:
    """Create a parameter template (e.g. 'Thread Size', 'Material', 'Length').

    Templates define what parameters can be assigned to parts.
    - units: measurement units (e.g. 'mm', 'inches', 'ohms')
    - choices: comma-separated valid values (e.g. 'Red,Green,Blue')
    - checkbox: if true, the parameter is a boolean toggle
    """

    @sync_to_async
    def _create():
        from part.models import PartParameterTemplate

        fields = {"name": name}
        if units:
            fields["units"] = units
        if description:
            fields["description"] = description
        if choices:
            fields["choices"] = choices
        if checkbox:
            fields["checkbox"] = checkbox
        tmpl = PartParameterTemplate.objects.create(**fields)
        return serialize_parameter_template(tmpl)

    return to_json(await _create())


@mcp.tool()
async def delete_parameter_template(id: int) -> str:
    """Delete a parameter template. Fails if any parts still use it."""

    @sync_to_async
    def _delete():
        from part.models import PartParameterTemplate

        try:
            tmpl = PartParameterTemplate.objects.get(pk=id)
        except PartParameterTemplate.DoesNotExist:
            return f"Parameter template {id} not found."
        tmpl.delete()
        return f"Parameter template {id} ('{tmpl.name}') deleted successfully."

    return await _delete()


# ---------------------------------------------------------------------------
# Part Parameters (values on individual parts)
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_part_parameters(part: int) -> str:
    """Get all parameter values for a specific part.

    Returns template info (name, units) alongside each value.
    """

    @sync_to_async
    def _query():
        from part.models import Part, PartParameter

        try:
            p = Part.objects.get(pk=part)
        except Part.DoesNotExist:
            return {"error": f"Part {part} not found"}
        params = list(
            PartParameter.objects.filter(part=p).select_related("template")
        )
        return [serialize_part_parameter(param) for param in params]

    results = await _query()
    if isinstance(results, dict):
        return to_json(results)
    return to_json({"count": len(results), "results": results})


@mcp.tool()
async def set_part_parameter(part: int, template: int, value: str) -> str:
    """Set (or update) a parameter value on a part.

    Uses upsert — creates the parameter if it doesn't exist, updates if it does.
    - part: Part ID
    - template: ParameterTemplate ID (use list_parameter_templates to find it)
    - value: the parameter value as a string
    """

    @sync_to_async
    def _upsert():
        from part.models import Part, PartParameter, PartParameterTemplate

        try:
            p = Part.objects.get(pk=part)
        except Part.DoesNotExist:
            return {"error": f"Part {part} not found"}
        try:
            tmpl = PartParameterTemplate.objects.get(pk=template)
        except PartParameterTemplate.DoesNotExist:
            return {"error": f"Parameter template {template} not found"}

        param, created = PartParameter.objects.update_or_create(
            part=p,
            template=tmpl,
            defaults={"data": value},
        )
        result = serialize_part_parameter(param)
        result["created"] = created
        return result

    return to_json(await _upsert())


@mcp.tool()
async def bulk_set_part_parameters(
    assignments: list[dict],
) -> str:
    """Set parameter values on multiple parts in one call (batch upsert).

    Each entry in assignments must be a dict with keys:
      - part: Part ID (int)
      - template: ParameterTemplate ID (int)
      - value: the parameter value (str)

    Example:
      assignments = [
        {"part": 10, "template": 4, "value": "1/4-20"},
        {"part": 10, "template": 7, "value": "Steel"},
        {"part": 11, "template": 4, "value": "#8-32"},
      ]

    Returns a summary with counts and any errors per entry.
    """

    @sync_to_async
    def _bulk_upsert():
        from django.db import transaction
        from part.models import Part, PartParameter, PartParameterTemplate

        # Collect all unique IDs to validate upfront
        part_ids = {a["part"] for a in assignments if "part" in a}
        tmpl_ids = {a["template"] for a in assignments if "template" in a}

        existing_parts = {p.pk: p for p in Part.objects.filter(pk__in=part_ids)}
        existing_tmpls = {
            t.pk: t for t in PartParameterTemplate.objects.filter(pk__in=tmpl_ids)
        }

        results = []
        to_create = []
        to_update = []

        # Look up existing parameters for update-or-create logic
        existing_params = {}
        for pp in PartParameter.objects.filter(
            part_id__in=part_ids, template_id__in=tmpl_ids
        ).select_related("template"):
            existing_params[(pp.part_id, pp.template_id)] = pp

        for i, entry in enumerate(assignments):
            part_id = entry.get("part")
            tmpl_id = entry.get("template")
            value = entry.get("value", "")

            if part_id not in existing_parts:
                results.append({"index": i, "error": f"Part {part_id} not found"})
                continue
            if tmpl_id not in existing_tmpls:
                results.append(
                    {"index": i, "error": f"Template {tmpl_id} not found"}
                )
                continue

            key = (part_id, tmpl_id)
            if key in existing_params:
                pp = existing_params[key]
                pp.data = value
                to_update.append(pp)
                results.append(
                    {
                        "index": i,
                        "part": part_id,
                        "template": tmpl_id,
                        "value": value,
                        "action": "updated",
                    }
                )
            else:
                pp = PartParameter(
                    part=existing_parts[part_id],
                    template=existing_tmpls[tmpl_id],
                    data=value,
                )
                to_create.append(pp)
                existing_params[key] = pp  # prevent dupes within batch
                results.append(
                    {
                        "index": i,
                        "part": part_id,
                        "template": tmpl_id,
                        "value": value,
                        "action": "created",
                    }
                )

        with transaction.atomic():
            if to_create:
                PartParameter.objects.bulk_create(to_create)
            if to_update:
                PartParameter.objects.bulk_update(to_update, ["data"])

        created = sum(1 for r in results if r.get("action") == "created")
        updated = sum(1 for r in results if r.get("action") == "updated")
        errors = sum(1 for r in results if "error" in r)
        return {
            "total": len(assignments),
            "created": created,
            "updated": updated,
            "errors": errors,
            "details": results,
        }

    return to_json(await _bulk_upsert())


@mcp.tool()
async def delete_part_parameter(part: int, template: int) -> str:
    """Remove a parameter value from a part.

    - part: Part ID
    - template: ParameterTemplate ID
    """

    @sync_to_async
    def _delete():
        from part.models import Part, PartParameter, PartParameterTemplate

        try:
            Part.objects.get(pk=part)
        except Part.DoesNotExist:
            return f"Part {part} not found."
        try:
            tmpl = PartParameterTemplate.objects.get(pk=template)
        except PartParameterTemplate.DoesNotExist:
            return f"Parameter template {template} not found."

        deleted, _ = PartParameter.objects.filter(
            part_id=part, template=tmpl
        ).delete()
        if deleted:
            return f"Parameter '{tmpl.name}' removed from part {part}."
        return f"Part {part} does not have parameter '{tmpl.name}'."

    return await _delete()


# ---------------------------------------------------------------------------
# Category Default Parameters
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_category_parameters(category: int) -> str:
    """List default parameter templates assigned to a part category.

    These are parameter slots that get pre-populated when creating parts
    in this category.
    """

    @sync_to_async
    def _query():
        from part.models import PartCategory, PartCategoryParameterTemplate

        try:
            PartCategory.objects.get(pk=category)
        except PartCategory.DoesNotExist:
            return {"error": f"Part category {category} not found"}
        cat_params = list(
            PartCategoryParameterTemplate.objects.filter(
                category_id=category
            ).select_related("parameter_template")
        )
        return [serialize_category_parameter(cp) for cp in cat_params]

    results = await _query()
    if isinstance(results, dict):
        return to_json(results)
    return to_json({"count": len(results), "results": results})


@mcp.tool()
async def set_category_parameter(
    category: int, template: int, default_value: str = ""
) -> str:
    """Assign a default parameter template to a category (upsert).

    When parts are created in this category, they'll get this parameter
    pre-populated with the default_value.
    - category: PartCategory ID
    - template: ParameterTemplate ID
    - default_value: default value for the parameter (can be empty)
    """

    @sync_to_async
    def _upsert():
        from part.models import (
            PartCategory,
            PartCategoryParameterTemplate,
            PartParameterTemplate,
        )

        try:
            PartCategory.objects.get(pk=category)
        except PartCategory.DoesNotExist:
            return {"error": f"Part category {category} not found"}
        try:
            tmpl = PartParameterTemplate.objects.get(pk=template)
        except PartParameterTemplate.DoesNotExist:
            return {"error": f"Parameter template {template} not found"}

        cat_param, created = PartCategoryParameterTemplate.objects.update_or_create(
            category_id=category,
            parameter_template=tmpl,
            defaults={"default_value": default_value},
        )
        result = serialize_category_parameter(cat_param)
        result["created"] = created
        return result

    return to_json(await _upsert())


@mcp.tool()
async def delete_category_parameter(category: int, template: int) -> str:
    """Remove a default parameter template from a category.

    - category: PartCategory ID
    - template: ParameterTemplate ID
    """

    @sync_to_async
    def _delete():
        from part.models import (
            PartCategory,
            PartCategoryParameterTemplate,
            PartParameterTemplate,
        )

        try:
            PartCategory.objects.get(pk=category)
        except PartCategory.DoesNotExist:
            return f"Part category {category} not found."
        try:
            tmpl = PartParameterTemplate.objects.get(pk=template)
        except PartParameterTemplate.DoesNotExist:
            return f"Parameter template {template} not found."

        deleted, _ = PartCategoryParameterTemplate.objects.filter(
            category_id=category, parameter_template=tmpl
        ).delete()
        if deleted:
            return f"Default parameter '{tmpl.name}' removed from category {category}."
        return f"Category {category} does not have default parameter '{tmpl.name}'."

    return await _delete()


# ---------------------------------------------------------------------------
# Stock Location Types
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_location_types(search: str = "", limit: int = 50) -> str:
    """List or search stock location types (e.g. 'Shelf', 'Bin', 'Room').

    Location types classify stock locations. Set search="" to list all.
    """

    @sync_to_async
    def _query():
        from stock.models import StockLocationType

        qs = StockLocationType.objects.all()
        if search:
            from django.db.models import Q

            qs = qs.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        lim = limit if limit > 0 else 50
        types = list(qs.order_by("name")[:lim])
        return [serialize_location_type(t) for t in types]

    results = await _query()
    return to_json({"count": len(results), "results": results})


@mcp.tool()
async def create_location_type(
    name: str, description: str = "", icon: str = ""
) -> str:
    """Create a stock location type (e.g. 'Shelf', 'Bin', 'Room', 'Parts Case').

    Location types classify stock locations. Once created, assign them to
    locations via create_stock_location or update_stock_location.
    Icon should be a Tabler icon string like 'ti:box:outline'.
    """
    if icon:
        valid, err = validate_icon(icon)
        if not valid:
            return to_json({"error": err})

    @sync_to_async
    def _create():
        from stock.models import StockLocationType

        fields = {"name": name}
        if description:
            fields["description"] = description
        if icon:
            fields["icon"] = icon
        loc_type = StockLocationType.objects.create(**fields)
        return serialize_location_type(loc_type)

    return to_json(await _create())


@mcp.tool()
async def delete_location_type(id: int) -> str:
    """Delete a stock location type."""

    @sync_to_async
    def _delete():
        from stock.models import StockLocationType

        try:
            loc_type = StockLocationType.objects.get(pk=id)
        except StockLocationType.DoesNotExist:
            return f"Location type {id} not found."
        loc_type.delete()
        return f"Location type {id} ('{loc_type.name}') deleted successfully."

    return await _delete()

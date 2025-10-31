"""Schema generation utilities for msgspec structs."""

from __future__ import annotations

import logging
from typing import Any

import msgspec

logger = logging.getLogger(__name__)


def generate_struct_schemas(
    structs: dict[str, type[msgspec.Struct]],
) -> dict[str, dict[str, Any]]:
    """
    Generate JSON schemas for msgspec.Struct types.

    Returns:
        Dict mapping struct names to their JSON schemas
    """
    if not structs:
        return {}

    try:
        struct_list = list(structs.values())
        schemas, components = msgspec.json.schema_components(
            struct_list,
            ref_template="#/components/schemas/{name}",
        )

        all_schemas: dict[str, dict[str, Any]] = {}

        for schema, struct in zip(schemas, struct_list):
            all_schemas[struct.__name__] = schema

        all_schemas.update(components)

        logger.debug(
            "Generated %d schemas using msgspec.json.schema_components",
            len(all_schemas),
        )
        return all_schemas

    except Exception as e:
        logger.error("Failed to generate schemas: %s", e, exc_info=True)
        return {}

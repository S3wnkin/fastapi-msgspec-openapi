"""OpenAPI response schema updater."""

from __future__ import annotations

import logging
from typing import Any, get_type_hints

import msgspec
from fastapi import FastAPI
from fastapi.routing import APIRoute

from fastapi_msgspec_openapi.scanner import extract_struct

logger = logging.getLogger(__name__)


def _update_method_response(
    path: str,
    method: str,
    return_type: Any,
    status_code: int,
    paths: dict[str, Any],
    openapi_schema: dict[str, Any],
) -> None:
    """
    Update a single method response schema to reference a msgspec.Struct.

    Always overrides existing response schemas with msgspec.Struct references.

    Args:
        path: Route path
        method: HTTP method (lowercase)
        return_type: Full return type annotation
        status_code: HTTP status code
        paths: OpenAPI paths dictionary
        openapi_schema: Full OpenAPI schema for components updates
    """
    if method not in paths[path]:
        logger.debug("Method %s not in path %s", method.upper(), path)
        return

    endpoint_schema = paths[path][method]
    responses = endpoint_schema.get("responses", {})
    status_str = str(status_code)

    if status_str not in responses:
        logger.debug(
            "Status code %s not in responses for %s %s",
            status_str,
            method.upper(),
            path,
        )
        return

    description = responses[status_str].get("description", "Successful Response")

    (schema,), components = msgspec.json.schema_components(
        (return_type,),
        ref_template="#/components/schemas/{name}",
    )

    if components:
        schemas = openapi_schema.setdefault("components", {}).setdefault("schemas", {})
        schemas.update(components)

    endpoint_schema["responses"][status_str] = {
        "description": description,
        "content": {"application/json": {"schema": schema}},
    }

    logger.debug(
        "Updated %s %s response %s with msgspec schema",
        method.upper(),
        path,
        status_str,
    )


def update_route_responses(
    openapi_schema: dict[str, Any],
    app: FastAPI,
) -> None:
    """
    Update route response schemas to reference msgspec.Struct schemas.

    Overrides any existing response schemas with msgspec.Struct references.
    """
    paths = openapi_schema.get("paths", {})

    for route in app.routes:
        if not isinstance(route, APIRoute) or route.endpoint is None:
            continue

        try:
            hints = get_type_hints(route.endpoint, include_extras=True)
            return_type = hints.get("return")
            if not return_type:
                continue

            struct = extract_struct(return_type)
            if not struct:
                continue

            path = route.path
            if path not in paths:
                logger.debug("Path %s not in OpenAPI schema", path)
                continue

            status_code = route.status_code or 200

            for method in route.methods:
                _update_method_response(
                    path=path,
                    method=method.lower(),
                    return_type=return_type,
                    status_code=status_code,
                    paths=paths,
                    openapi_schema=openapi_schema,
                )

        except (NameError, AttributeError) as e:
            logger.debug(
                "Cannot resolve type hints for %s: %s (skipping route)",
                route.endpoint.__name__ if route.endpoint is not None else "unknown",
                e,
            )
            continue
        except Exception as e:
            logger.error(
                "Failed to update response for %s: %s",
                route.endpoint.__name__ if route.endpoint is not None else "unknown",
                e,
                exc_info=True,
            )

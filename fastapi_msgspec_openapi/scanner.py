"""Route scanning and struct extraction utilities."""

from __future__ import annotations

import inspect
import logging
from functools import cache
from typing import Any, get_args, get_origin, get_type_hints

import msgspec
from fastapi import FastAPI
from fastapi.routing import APIRoute

logger = logging.getLogger(__name__)


@cache
def is_struct(tp: Any) -> bool:
    """Check if type is a msgspec.Struct subclass"""
    try:
        return inspect.isclass(tp) and issubclass(tp, msgspec.Struct)
    except TypeError:
        return False


def extract_struct(annotation: Any, *, depth: int = 0) -> type[msgspec.Struct] | None:
    """
    Recursively extract msgspec.Struct from type annotation.

    Handles direct types, generics, and nested generics.

    Args:
        annotation: Type annotation to analyze
        depth: Recursion depth limiter

    Returns:
        First msgspec.Struct found, or None
    """
    if depth > 10:
        logger.debug("Max recursion depth reached for type extraction")
        return None

    if is_struct(annotation):
        return annotation  # type: ignore[no-any-return]

    origin = get_origin(annotation)
    if origin is None:
        return None

    for arg in get_args(annotation):
        if struct := extract_struct(arg, depth=depth + 1):
            return struct

    return None


def scan_routes(app: FastAPI) -> dict[str, type[msgspec.Struct]]:
    """
    Scan all FastAPI routes for msgspec.Struct types.

    Returns:
        Dict mapping struct names to struct classes
    """
    structs: dict[str, type[msgspec.Struct]] = {}

    for route in app.routes:
        if not isinstance(route, APIRoute) or route.endpoint is None:
            continue

        try:
            hints = get_type_hints(route.endpoint, include_extras=True)
        except (NameError, AttributeError) as e:
            logger.debug(
                "Cannot resolve type hints for %s: %s (skipping route)",
                route.endpoint.__name__,
                e,
            )
            continue
        except Exception as e:
            logger.debug(
                "Failed to get type hints for %s: %s",
                route.endpoint.__name__,
                e,
            )
            continue

        for param_name, annotation in hints.items():
            if struct := extract_struct(annotation):
                if struct.__name__ not in structs:
                    structs[struct.__name__] = struct
                    logger.debug(
                        "Found msgspec.Struct '%s' in %s (param: %s)",
                        struct.__name__,
                        route.endpoint.__name__,
                        param_name,
                    )

    return structs

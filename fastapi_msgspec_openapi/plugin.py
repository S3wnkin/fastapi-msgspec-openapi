"""Main plugin class for FastAPI msgspec OpenAPI integration."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from fastapi_msgspec_openapi.scanner import scan_routes
from fastapi_msgspec_openapi.schema import generate_struct_schemas
from fastapi_msgspec_openapi.updater import update_route_responses

logger = logging.getLogger(__name__)


def _generate_openapi(app: FastAPI) -> dict[str, Any]:
    """Generate OpenAPI schema with msgspec.Struct support."""
    if app.openapi_schema:
        logger.debug("Returning cached OpenAPI schema")
        return app.openapi_schema

    logger.info("Generating OpenAPI schema with msgspec support")

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    structs = scan_routes(app)

    if not structs:
        logger.info("No msgspec.Struct types found")
        app.openapi_schema = openapi_schema
        return openapi_schema

    openapi_schema.setdefault("components", {}).setdefault("schemas", {})

    schemas = generate_struct_schemas(structs)
    openapi_schema["components"]["schemas"].update(schemas)

    update_route_responses(openapi_schema, app)

    logger.info("OpenAPI schema generated with msgspec support")

    app.openapi_schema = openapi_schema
    return openapi_schema


class MsgSpecPlugin:
    """
    FastAPI plugin for msgspec.Struct OpenAPI integration.

    Automatically detects msgspec.Struct types in route signatures and
    generates OpenAPI schemas for seamless TypeScript type generation.

    Note:
        Struct types must be defined at module level (not inside functions)
        for proper type hint resolution. This is standard Python practice.

    Example:
        app = FastAPI()

        @app.get("/user", response_model=Any)
        async def get_user() -> User:
            return msgspec.to_builtins(User(id=1, name="Alice"))

        MsgSpecPlugin.inject(app)

        # Generate TypeScript types:
        # npx openapi-typescript http://localhost:8000/openapi.json -o api-types.ts
    """

    @classmethod
    def inject(cls, app: FastAPI) -> None:
        """
        Inject msgspec OpenAPI support into FastAPI application.

        This method overrides the app.openapi() method to include
        msgspec.Struct schema generation in the OpenAPI specification.

        Args:
            app: FastAPI application instance to inject into
        """
        app.openapi = lambda: _generate_openapi(app)  # type: ignore[method-assign]
        logger.info("MsgSpecPlugin injected into FastAPI application")

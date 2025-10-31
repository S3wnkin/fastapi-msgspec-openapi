"""
FastAPI msgspec OpenAPI Plugin

Integrates msgspec.Struct types into FastAPI's OpenAPI schema generation.
Automatically detects msgspec structs from type hints and generates schemas.

Usage:
    from typing import Any

    from fastapi import FastAPI
    from fastapi_msgspec_openapi import MsgSpecPlugin

    app = FastAPI()

    @app.get("/user", response_model=Any)
    async def get_user() -> User:
        return msgspec.to_builtins(User(id=1, name="Alice"))

    MsgSpecPlugin.inject(app)
"""

from fastapi_msgspec_openapi.plugin import MsgSpecPlugin
from fastapi_msgspec_openapi.scanner import extract_struct, is_struct, scan_routes
from fastapi_msgspec_openapi.schema import generate_struct_schemas

__version__ = "0.1.0"

__all__ = [
    "MsgSpecPlugin",
    "extract_struct",
    "is_struct",
    "scan_routes",
    "generate_struct_schemas",
]

"""
Test suite for FastAPI msgspec OpenAPI Plugin

Run with: pytest tests/ -v
"""

from __future__ import annotations

from typing import Any, Optional

import msgspec
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_msgspec_openapi import (
    MsgSpecPlugin,
    extract_struct,
    generate_struct_schemas,
    is_struct,
    scan_routes,
)


# Test fixtures - msgspec structs (defined at module level)
class SimpleStruct(msgspec.Struct):
    id: int
    name: str


class NestedStruct(msgspec.Struct):
    coins: int | None = 0
    gems: int | None = 0


class ParentStruct(msgspec.Struct):
    balance: NestedStruct
    error: str | None = None


class GenericResponse(msgspec.Struct):
    success: bool
    data: dict | None = None


# Test structs for nested hierarchy test
class Level3(msgspec.Struct):
    value: int


class Level2(msgspec.Struct):
    level3: Level3


class Level1(msgspec.Struct):
    level2: Level2


# Tests for utility functions


def test_is_struct_with_valid_struct():
    """Test is_struct identifies msgspec.Struct correctly"""
    assert is_struct(SimpleStruct) is True


def test_is_struct_with_invalid_types():
    """Test is_struct rejects non-struct types"""
    assert is_struct(int) is False
    assert is_struct(str) is False
    assert is_struct(dict) is False
    assert is_struct(None) is False


def test_extract_struct_direct():
    """Test extracting struct from direct type annotation"""
    result = extract_struct(SimpleStruct)
    assert result is SimpleStruct


def test_extract_struct_from_optional():
    """Test extracting struct from Optional type"""
    from typing import Optional

    result = extract_struct(Optional[SimpleStruct])
    assert result is SimpleStruct


def test_extract_struct_from_list():
    """Test extracting struct from List type"""
    result = extract_struct(list[SimpleStruct])
    assert result is SimpleStruct


def test_extract_struct_from_nested_generic():
    """Test extracting struct from nested generic like list[Optional[Struct]]"""
    from typing import Optional

    result = extract_struct(list[Optional[SimpleStruct]])
    assert result is SimpleStruct


def test_extract_struct_none_for_primitives():
    """Test extract_struct returns None for primitive types"""
    assert extract_struct(int) is None
    assert extract_struct(str) is None
    assert extract_struct(dict) is None


def test_extract_struct_depth_limit():
    """Test recursion depth limit prevents infinite loops"""
    # This shouldn't crash even with deep nesting
    result = extract_struct(
        list[list[list[list[list[list[list[list[list[list[list[int]]]]]]]]]]]
    )
    assert result is None


# Tests for schema generation


def test_generate_struct_schemas_single():
    """Test schema generation for single struct"""
    structs = {"SimpleStruct": SimpleStruct}
    schemas = generate_struct_schemas(structs)

    assert "SimpleStruct" in schemas
    assert "properties" in schemas["SimpleStruct"]
    assert "id" in schemas["SimpleStruct"]["properties"]
    assert "name" in schemas["SimpleStruct"]["properties"]


def test_generate_struct_schemas_nested():
    """Test schema generation includes nested structs"""
    structs = {"ParentStruct": ParentStruct}
    schemas = generate_struct_schemas(structs)

    # Should include both parent and nested struct
    assert "ParentStruct" in schemas
    assert "NestedStruct" in schemas
    assert len(schemas) >= 2


def test_generate_struct_schemas_empty():
    """Test schema generation with no structs"""
    schemas = generate_struct_schemas({})
    assert schemas == {}


def test_generate_struct_schemas_uses_ref_template():
    """Test schemas use OpenAPI ref template"""
    structs = {"ParentStruct": ParentStruct}
    schemas = generate_struct_schemas(structs)

    # Check that nested references use proper OpenAPI format
    parent_schema = schemas["ParentStruct"]
    balance_prop = parent_schema["properties"]["balance"]

    # Should have a $ref to the nested struct
    if "$ref" in balance_prop:
        assert "#/components/schemas/" in balance_prop["$ref"]


# Tests for route scanning


def test_scan_routes_finds_return_type():
    """Test scanning finds structs in return types"""
    app = FastAPI()

    @app.get("/test", response_model=Any)
    async def get_test() -> SimpleStruct:
        return msgspec.to_builtins(SimpleStruct(id=1, name="test"))

    structs = scan_routes(app)
    assert "SimpleStruct" in structs
    assert structs["SimpleStruct"] is SimpleStruct


def test_scan_routes_multiple_endpoints():
    """Test scanning finds structs across multiple endpoints"""
    app = FastAPI()

    @app.get("/simple", response_model=Any)
    async def get_simple() -> SimpleStruct:
        return msgspec.to_builtins(SimpleStruct(id=1, name="test"))

    @app.get("/parent", response_model=Any)
    async def get_parent() -> ParentStruct:
        return msgspec.to_builtins(ParentStruct(balance=NestedStruct()))

    structs = scan_routes(app)
    assert "SimpleStruct" in structs
    assert "ParentStruct" in structs


def test_scan_routes_ignores_non_struct_routes():
    """Test scanning ignores routes without msgspec structs"""
    app = FastAPI()

    @app.get("/test")
    async def get_test() -> dict:
        return {"test": "data"}

    structs = scan_routes(app)
    assert len(structs) == 0


def test_scan_routes_deduplicates():
    """Test scanning doesn't duplicate same struct from multiple routes"""
    app = FastAPI()

    @app.get("/test1", response_model=Any)
    async def get_test1() -> SimpleStruct:
        return msgspec.to_builtins(SimpleStruct(id=1, name="test"))

    @app.get("/test2", response_model=Any)
    async def get_test2() -> SimpleStruct:
        return msgspec.to_builtins(SimpleStruct(id=2, name="test2"))

    structs = scan_routes(app)
    assert len(structs) == 1
    assert "SimpleStruct" in structs


# Tests for plugin integration


def test_plugin_inject_modifies_openapi():
    """Test plugin injection modifies app.openapi method"""
    app = FastAPI()
    original_openapi = app.openapi

    MsgSpecPlugin.inject(app)

    # Should have replaced the openapi method
    assert app.openapi != original_openapi


def test_plugin_generates_valid_openapi():
    """Test plugin generates valid OpenAPI schema"""
    app = FastAPI()

    @app.get("/test", response_model=Any)
    async def get_test() -> SimpleStruct:
        return msgspec.to_builtins(SimpleStruct(id=1, name="test"))

    MsgSpecPlugin.inject(app)

    openapi_schema = app.openapi()

    assert "components" in openapi_schema
    assert "schemas" in openapi_schema["components"]
    assert "SimpleStruct" in openapi_schema["components"]["schemas"]


def test_plugin_updates_response_schema():
    """Test plugin updates endpoint response to reference struct"""
    app = FastAPI()

    @app.get("/test", response_model=Any)
    async def get_test() -> SimpleStruct:
        return msgspec.to_builtins(SimpleStruct(id=1, name="test"))

    MsgSpecPlugin.inject(app)

    openapi_schema = app.openapi()
    response_schema = openapi_schema["paths"]["/test"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]

    assert "$ref" in response_schema
    assert "SimpleStruct" in response_schema["$ref"]


def test_plugin_handles_nested_structs():
    """Test plugin properly handles nested struct schemas"""
    app = FastAPI()

    @app.get("/balance", response_model=Any)
    async def get_balance() -> ParentStruct:
        return msgspec.to_builtins(
            ParentStruct(balance=NestedStruct(coins=100, gems=50))
        )

    MsgSpecPlugin.inject(app)

    openapi_schema = app.openapi()

    # Both structs should be in components
    assert "ParentStruct" in openapi_schema["components"]["schemas"]
    assert "NestedStruct" in openapi_schema["components"]["schemas"]

    # Response should reference parent
    response_schema = openapi_schema["paths"]["/balance"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert "ParentStruct" in response_schema["$ref"]


def test_plugin_handles_multi_method_routes():
    """Test plugin handles routes with multiple HTTP methods"""
    app = FastAPI()

    @app.api_route("/test", methods=["GET", "POST"], response_model=Any)
    async def test_route() -> SimpleStruct:
        return msgspec.to_builtins(SimpleStruct(id=1, name="test"))

    MsgSpecPlugin.inject(app)

    openapi_schema = app.openapi()

    # Both methods should have the schema reference
    for method in ["get", "post"]:
        response_schema = openapi_schema["paths"]["/test"][method]["responses"]["200"][
            "content"
        ]["application/json"]["schema"]
        assert "$ref" in response_schema
        assert "SimpleStruct" in response_schema["$ref"]


def test_plugin_caches_schema():
    """Test plugin caches generated schema"""
    app = FastAPI()

    @app.get("/test", response_model=Any)
    async def get_test() -> SimpleStruct:
        return msgspec.to_builtins(SimpleStruct(id=1, name="test"))

    MsgSpecPlugin.inject(app)

    # First call generates schema
    schema1 = app.openapi()
    # Second call should return cached schema
    schema2 = app.openapi()

    # Should be the exact same object (cached)
    assert schema1 is schema2


def test_plugin_with_no_structs():
    """Test plugin handles apps without msgspec structs gracefully"""
    app = FastAPI()

    @app.get("/test")
    async def get_test() -> dict:
        return {"test": "data"}

    MsgSpecPlugin.inject(app)

    openapi_schema = app.openapi()

    # Should still generate valid schema, just without custom structs
    assert "openapi" in openapi_schema
    assert "paths" in openapi_schema


def test_plugin_with_testclient():
    """Test plugin works with FastAPI TestClient"""
    app = FastAPI()

    @app.get("/test", response_model=Any)
    async def get_test() -> SimpleStruct:
        return msgspec.to_builtins(SimpleStruct(id=1, name="test"))

    MsgSpecPlugin.inject(app)

    client = TestClient(app)

    # Test OpenAPI endpoint
    response = client.get("/openapi.json")
    assert response.status_code == 200

    openapi_schema = response.json()
    assert "SimpleStruct" in openapi_schema["components"]["schemas"]


def test_plugin_overrides_existing_schema():
    """Test plugin overrides FastAPI's auto-generated schemas"""
    app = FastAPI()

    @app.get("/test", response_model=Any)
    async def get_test() -> ParentStruct:
        return msgspec.to_builtins(
            ParentStruct(balance=NestedStruct(coins=100, gems=50))
        )

    MsgSpecPlugin.inject(app)

    openapi_schema = app.openapi()

    # Should have proper $ref, not generic schema
    response_schema = openapi_schema["paths"]["/test"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]

    assert "$ref" in response_schema
    assert "#/components/schemas/ParentStruct" in response_schema["$ref"]


def test_plugin_with_optional_return():
    """Test plugin handles Optional[Struct] return types"""
    app = FastAPI()

    @app.get("/test", response_model=Any)
    async def get_test() -> Optional[SimpleStruct]:
        return msgspec.to_builtins(SimpleStruct(id=1, name="test"))

    MsgSpecPlugin.inject(app)

    openapi_schema = app.openapi()

    # Should still detect and use the struct
    assert "SimpleStruct" in openapi_schema["components"]["schemas"]


def test_plugin_with_list_return():
    """Test plugin handles list[Struct] return types"""
    app = FastAPI()

    @app.get("/test", response_model=Any)
    async def get_test() -> list[SimpleStruct]:
        return [msgspec.to_builtins(SimpleStruct(id=1, name="test"))]

    MsgSpecPlugin.inject(app)

    openapi_schema = app.openapi()

    # Should detect the struct inside the list
    assert "SimpleStruct" in openapi_schema["components"]["schemas"]


# Performance and edge case tests


def test_plugin_with_many_routes():
    """Test plugin handles apps with many routes efficiently"""
    app = FastAPI()

    # Create 50 routes with proper response_model
    for i in range(50):
        # Use a closure to capture the current value of i
        def make_handler(route_id):
            async def handler() -> SimpleStruct:
                return msgspec.to_builtins(
                    SimpleStruct(id=route_id, name=f"test{route_id}")
                )

            return handler

        app.get(f"/test{i}", response_model=Any)(make_handler(i))

    MsgSpecPlugin.inject(app)

    openapi_schema = app.openapi()

    # Should still work correctly
    assert "SimpleStruct" in openapi_schema["components"]["schemas"]
    assert len(openapi_schema["paths"]) == 50


def test_plugin_with_complex_nested_structs():
    """Test plugin handles deeply nested struct hierarchies"""
    app = FastAPI()

    @app.get("/test", response_model=Any)
    async def get_test() -> Level1:
        return msgspec.to_builtins(Level1(level2=Level2(level3=Level3(value=42))))

    MsgSpecPlugin.inject(app)

    openapi_schema = app.openapi()

    # All levels should be in schemas
    assert "Level1" in openapi_schema["components"]["schemas"]
    assert "Level2" in openapi_schema["components"]["schemas"]
    assert "Level3" in openapi_schema["components"]["schemas"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# fastapi-msgspec-openapi

[![PyPI version](https://badge.fury.io/py/fastapi-msgspec-openapi.svg)](https://pypi.org/project/fastapi-msgspec-openapi/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/S3wnkin/fastapi-msgspec-openapi/workflows/Tests/badge.svg)](https://github.com/S3wnkin/fastapi-msgspec-openapi/actions)

FastAPI plugin for automatic OpenAPI schema generation from [msgspec](https://github.com/jcrist/msgspec) structs. Enables Swagger UI documentation and TypeScript type generation.

## Features

- ✨ **Automatic OpenAPI schema generation** from msgspec structs
- 📝 **Swagger UI integration** - See your msgspec types in `/docs`
- 🔷 **TypeScript type generation** support via `openapi-typescript`
- 🚀 **Zero runtime overhead** - Schema generation happens once at startup
- 🎯 **Type-safe** - Full type hints and mypy compatibility
- 🔧 **Easy integration** - Single line of code to enable

## Installation

```bash
pip install fastapi-msgspec-openapi
```

## Quick Start

```python
from typing import Any
from fastapi import FastAPI
import msgspec
from fastapi_msgspec_openapi import MsgSpecPlugin

# Define your msgspec structs
class User(msgspec.Struct):
    id: int
    name: str
    email: str

app = FastAPI()

# Inject the plugin
MsgSpecPlugin.inject(app)

@app.get("/user", response_model=Any)
async def get_user() -> User:
    return msgspec.to_builtins(User(id=1, name="Alice", email="alice@example.com"))
```

Now visit `/docs` - your msgspec structs will appear in the Swagger UI! 🎉

## Why Use This?

[msgspec](https://github.com/jcrist/msgspec) is one of the fastest Python serialization libraries, but FastAPI doesn't natively generate OpenAPI schemas for msgspec structs. This plugin bridges that gap.

### Perfect Combo with `fastapi-msgspec`

This plugin works great alongside [fastapi-msgspec](https://github.com/iurii-skorniakov/fastapi-msgspec) for complete msgspec integration:

```python
from fastapi import FastAPI
from fastapi_msgspec.responses import MsgSpecJSONResponse  # Fast serialization
from fastapi_msgspec_openapi import MsgSpecPlugin          # OpenAPI docs

app = FastAPI(default_response_class=MsgSpecJSONResponse)
MsgSpecPlugin.inject(app)

# Now you have both:
# ✅ Fast msgspec serialization (runtime performance)
# ✅ Full OpenAPI documentation (developer experience)
```

## Why msgspec Over Pydantic?

**Performance**: msgspec is significantly faster than Pydantic for serialization:

- 5-10x faster serialization
- Lower memory usage
- Native JSON encoding

**When to use this plugin**:

- ✅ High-throughput APIs
- ✅ Performance-critical services
- ✅ You want msgspec speed + OpenAPI docs
- ✅ TypeScript type generation needed

**When to stick with Pydantic**:

- ❌ Complex validation logic (Pydantic has richer validation)
- ❌ ORM integration (Pydantic works better with SQLAlchemy)
- ❌ You don't need extreme performance

## TypeScript Type Generation

Generate TypeScript types from your OpenAPI schema:

```bash
# Generate types
npx openapi-typescript http://localhost:8000/openapi.json -o api-types.ts
```

```typescript
// Use in your frontend
import type { components } from "./api-types";

type User = components["schemas"]["User"];

const user: User = {
  id: 1,
  name: "Alice",
  email: "alice@example.com",
};
```

## Advanced Usage

### Nested Structs

```python
class Address(msgspec.Struct):
    street: str
    city: str

class User(msgspec.Struct):
    id: int
    name: str
    address: Address  # Nested struct

@app.get("/user", response_model=Any)
async def get_user() -> User:
    return msgspec.to_builtins(
        User(
            id=1,
            name="Alice",
            address=Address(street="123 Main St", city="NYC")
        )
    )
```

Both `User` and `Address` schemas will be generated automatically!

### Optional and Generic Types

```python
from typing import Optional

class Response(msgspec.Struct):
    user: Optional[User] = None
    users: list[User] = []

@app.get("/response", response_model=Any)
async def get_response() -> Response:
    return msgspec.to_builtins(Response(users=[...]))
```

The plugin handles `Optional`, `list`, and other generic types automatically.

## How It Works

1. **Route scanning** - Detects msgspec structs in route type hints
2. **Schema generation** - Uses `msgspec.json.schema_components()` for native OpenAPI schemas
3. **Response updates** - Patches FastAPI's OpenAPI schema to reference your structs
4. **Caching** - Schema generation happens once, then cached

## Limitations & Design Decisions

### Why `response_model=Any`?

FastAPI tries to validate/serialize the response using Pydantic when you specify a `response_model`. Since we're using msgspec structs (not Pydantic models), we use `Any` to bypass FastAPI's response handling:

```python
@app.get("/user", response_model=Any)  # Tells FastAPI: "I'll handle serialization"
async def get_user() -> User:          # Plugin reads this for OpenAPI schema
    return msgspec.to_builtins(...)    # We handle serialization ourselves
```

The plugin reads the **return type hint** (`-> User`) for schema generation, while `response_model=Any` prevents FastAPI from interfering.

### Type Checker Warnings

You may see type checker warnings like:

```python
return msgspec.to_builtins(user)  # "Returning Any from function declared to return User"
```

This is expected - `msgspec.to_builtins()` returns `Any` because it converts to dict/list at runtime. You can suppress this with:

```python
return msgspec.to_builtins(user)  # type: ignore[return-value]
```

Or configure your type checker to ignore this pattern:

```toml
# pyproject.toml
[tool.mypy]
[[tool.mypy.overrides]]
module = "your_app.*"
disable_error_code = ["return-value"]
```

### Module-Level Struct Definitions

Structs must be defined at module level for Python's `get_type_hints()` to resolve them properly:

```python
# ✅ Good - Module level
class User(msgspec.Struct):
    id: int

# ❌ Bad - Inside function
def create_app():
    class User(msgspec.Struct):  # Won't be detected
        id: int
```

This is a Python limitation, not specific to this plugin.

### Why Not Use `response_model=User` Directly?

FastAPI's `response_model` expects Pydantic models. If we could use msgspec structs directly, we wouldn't need this plugin! The whole purpose is to:

1. Use msgspec for performance (serialization)
2. Generate OpenAPI schemas (documentation)
3. Keep type hints accurate (developer experience)

This plugin bridges the gap by extracting schemas from type hints while letting you handle serialization with msgspec.

## Requirements

- Python 3.10+
- FastAPI 0.100.0+
- msgspec 0.18.0+

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Credits

Created by [S3wnkin](https://github.com/S3wnkin)

Inspired by:

- [msgspec](https://github.com/jcrist/msgspec) by Jim Crist-Harif
- [FastAPI](https://github.com/tiangolo/fastapi) by Sebastián Ramírez
- [fastapi-msgspec](https://github.com/iurii-skorniakov/fastapi-msgspec) by Iurii Skorniakov

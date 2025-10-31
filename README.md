# fastapi-msgspec-openapi

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

## TypeScript Type Generation

Generate TypeScript types from your OpenAPI schema:

```bash
# Generate types
npx openapi-typescript http://localhost:8000/openapi.json -o api-types.ts
```

```typescript
// Use in your frontend
import type { components } from './api-types';

type User = components['schemas']['User'];

const user: User = {
  id: 1,
  name: "Alice",
  email: "alice@example.com"
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

## Requirements

- Python 3.10+
- FastAPI 0.100.0+
- msgspec 0.18.0+

## Important Notes

- ⚠️ **Struct types must be defined at module level** (not inside functions) for proper type hint resolution
- ⚠️ **Always use `response_model=Any`** in route decorators when returning msgspec structs
- ⚠️ **Use `msgspec.to_builtins()`** to serialize structs before returning

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Credits

Created by [RamsesDev](https://github.com/RamsesDev)

Inspired by:
- [msgspec](https://github.com/jcrist/msgspec) by Jim Crist-Harif
- [FastAPI](https://github.com/tiangolo/fastapi) by Sebastián Ramírez
- [fastapi-msgspec](https://github.com/iurii-skorniakov/fastapi-msgspec) by Iurii Skorniakov

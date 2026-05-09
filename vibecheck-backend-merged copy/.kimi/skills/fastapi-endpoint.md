# Skill: Create a FastAPI Endpoint

## Template

```python
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/venues", tags=["venues"])


class MyRequest(BaseModel):
    field1: str
    field2: int


class MyResponse(BaseModel):
    id: str
    field1: str
    field2: int
    computed: float


@router.post("/{venue_id}/my-action", response_model=MyResponse)
def my_action(venue_id: str, payload: MyRequest):
    """
    Description of what this endpoint does.
    """
    # Validate venue exists
    if venue_id not in VENUES:
        raise HTTPException(status_code=404, detail="Venue not found")

    # Business logic
    computed = payload.field2 * 2.5

    return MyResponse(
        id=venue_id,
        field1=payload.field1,
        field2=payload.field2,
        computed=computed,
    )
```

## How to Use

1. Save as `api-server/src/routes/my_route.py`
2. Register in `api-server/src/main.py`:

```python
from fastapi import FastAPI
from routes import my_route

app = FastAPI()
app.include_router(my_route.router)
```

3. Test:

```bash
curl -X POST http://localhost:8000/venues/venue-001/my-action \
  -H "Content-Type: application/json" \
  -d '{"field1": "hello", "field2": 10}'
```

## Patterns

- Use `APIRouter` for modularity.
- Use `response_model` for auto-documentation.
- Use `HTTPException` for errors.
- Use `Depends()` for shared dependencies (DB session, auth) when needed.

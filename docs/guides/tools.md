# Adding tools

This guide covers everything about defining tools and handling errors.

## Basic tool

```python
import solarium

@solarium.tool
def reverse_string(text: str) -> str:
    """Reverse the characters in a string."""
    return text[::-1]
```

That's it. Solarium generates the full JSON schema from the type hints and docstring.

## Multiple parameters

```python
@solarium.tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient."""
    # your SMTP logic here
    return f"Email sent to {to} with subject '{subject}'."
```

Parameters without defaults are marked `required` in the schema automatically.

## Optional parameters

```python
import inspect
from typing import Optional

@solarium.tool
def search(query: str, limit: int = 10) -> str:
    """Search for results. Limit defaults to 10."""
    return f"Top {limit} results for: {query}"
```

## Returning structured data

Return a dict — Solarium serializes it to JSON before sending to Claude:

```python
@solarium.tool
def get_user(user_id: str) -> dict:
    """Fetch a user record by ID."""
    return {
        "id": user_id,
        "name": "Alice",
        "email": "alice@example.com",
        "plan": "pro",
    }
```

## Error handling

Raise an exception inside a tool — Solarium catches it and sends the error message back to Claude, which will then decide how to handle it (retry with different args, apologize, etc.):

```python
@solarium.tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b
```

## Calling external APIs

```python
import httpx

@solarium.tool
def get_weather(city: str) -> str:
    """Get current weather for a city using the Open-Meteo API."""
    # geocode city to lat/lon first in a real implementation
    return f"Weather data for {city}: 72°F, partly cloudy."
```

## Sharing a registry across agents

```python
# shared_tools.py
import solarium

@solarium.tool
def lookup_product(sku: str) -> str:
    """Look up a product by SKU."""
    return f"Product {sku}: Widget Pro, $49.99, in stock."

shared = solarium.ToolRegistry()
shared.register(lookup_product)

# agent_a.py
from shared_tools import shared
agent_a = solarium.Agent(name="sales", tools=shared)

# agent_b.py
from shared_tools import shared
agent_b = solarium.Agent(name="support", tools=shared)
```

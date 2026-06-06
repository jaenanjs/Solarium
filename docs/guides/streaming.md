# Streaming responses

Streaming lets you display tokens as they arrive instead of waiting for the full response — great for chat interfaces and long outputs.

## Basic streaming

```python
import asyncio
import solarium

agent = solarium.Agent(name="writer", role="creative writer")

async def main():
    async for token in agent.astream("Write a short poem about the ocean."):
        print(token, end="", flush=True)
    print()  # newline at end

asyncio.run(main())
```

## Streaming in a web server (FastAPI)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import solarium

app = FastAPI()
agent = solarium.Agent(name="assistant", role="helpful assistant")

@app.get("/chat")
async def chat(message: str):
    async def token_stream():
        async for token in agent.astream(message):
            yield token

    return StreamingResponse(token_stream(), media_type="text/plain")
```

## Streaming in a CLI

```python
import asyncio
import solarium

agent = solarium.Agent(name="assistant", role="helpful assistant")

async def chat_loop():
    print("Solarium Chat — type 'quit' to exit\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":
            break
        print("Agent: ", end="", flush=True)
        async for token in agent.astream(user_input):
            print(token, end="", flush=True)
        print()

asyncio.run(chat_loop())
```

## Note on tool use

`astream` does not support tool use — it returns a single text response. For agents that need tools, use `arun` instead, which runs the full agentic loop and returns the complete final answer.

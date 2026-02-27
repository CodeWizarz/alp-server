import asyncio
import httpx
import json


async def run_test():
    url = "http://localhost:8000/v1/ingest"
    headers = {
        "X-API-Key": "demo-key",
        "X-Tenant-ID": "demo-tenant",
        "Content-Type": "application/json",
    }

    events = [
        {
            "tenant_id": "demo-tenant",
            "event_type": "llm_call",
            "payload": {"prompt": "Hello", "completion": "Hi there"},
            "function_name": "generate_greeting",
            "latency_ms": 150,
            "status": "success",
        },
        {
            "tenant_id": "demo-tenant",
            "event_type": "llm_call",
            "payload": {"prompt": "Crash", "error": "timeout"},
            "function_name": "generate_crash",
            "latency_ms": 5000,
            "status": "error",
        },
    ]

    print(f"Sending {len(events)} events to {url}...")
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=events)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")


if __name__ == "__main__":
    asyncio.run(run_test())

import asyncio
import httpx


async def test_graceful():
    url_ingest = "http://localhost:8000/v1/ingest"
    url_stats = "http://localhost:8000/v1/stats/errors"
    url_query = "http://localhost:8000/v1/query"
    url_health = "http://localhost:8000/health"

    headers = {
        "X-API-Key": "demo-key",
        "X-Tenant-ID": "demo-tenant",
    }

    async with httpx.AsyncClient() as client:
        print("\n--- Testing Health ---")
        resp = await client.get(url_health)
        print(f"Health Response: {resp.json()}")

        print("\n--- Testing Ingest ---")
        payload = [
            {
                "tenant_id": "demo-tenant",
                "event_type": "test_grace",
                "payload": {"test": "grace"},
                "function_name": "test_grace_func",
                "latency_ms": 10,
                "status": "success",
            }
        ]
        resp = await client.post(url_ingest, headers=headers, json=payload)
        print(
            f"Ingest Response ({resp.status_code}): {resp.json()} Headers: {dict(resp.headers)}"
        )

        print("\n--- Testing Stats ---")
        resp = await client.get(url_stats, headers=headers)
        print(
            f"Stats Response ({resp.status_code}): {resp.json()} Headers: {dict(resp.headers)}"
        )

        print("\n--- Testing Query ---")
        resp = await client.post(
            url_query, headers=headers, json={"tenant_id": "demo-tenant", "limit": 5}
        )
        print(
            f"Query Response ({resp.status_code}): {resp.json()} Headers: {dict(resp.headers)}"
        )


if __name__ == "__main__":
    asyncio.run(test_graceful())

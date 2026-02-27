import asyncio
import httpx


async def test_docker():
    url_health = "http://localhost:8080/health"
    url_ingest = "http://localhost:8080/v1/ingest"

    headers = {
        "X-API-Key": "demo-key",
        "X-Tenant-ID": "demo-tenant",
    }

    async with httpx.AsyncClient() as client:
        print("\n--- Testing Docker Health (Port 8080) ---")
        try:
            resp = await client.get(url_health)
            print(f"Health Response: {resp.json()}")
        except Exception as e:
            print(f"Health check failed: {e}")

        print("\n--- Testing Docker Ingest (Port 8080) ---")
        payload = [
            {
                "tenant_id": "demo-tenant",
                "event_type": "docker_test",
                "payload": {"container": "live"},
                "function_name": "verify_docker",
                "latency_ms": 50,
                "status": "success",
            }
        ]
        try:
            resp = await client.post(url_ingest, headers=headers, json=payload)
            print(f"Ingest Response ({resp.status_code}): {resp.json()}")
        except Exception as e:
            print(f"Ingest check failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_docker())

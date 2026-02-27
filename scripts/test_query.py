import asyncio
import httpx


async def run_query_test():
    url = "http://localhost:8000/v1/query"
    headers = {
        "X-API-Key": "demo-key",
        "X-Tenant-ID": "demo-tenant",
    }

    async with httpx.AsyncClient() as client:
        print("\n--- Testing Empty Query (All Events) ---")
        payload = {"tenant_id": "demo-tenant", "limit": 10}
        resp = await client.post(url, headers=headers, json=payload)
        print(f"Response ({resp.status_code}): {resp.json()}")

        print("\n--- Testing Filter by Function Name ---")
        payload = {
            "tenant_id": "demo-tenant",
            "function_name": "generate_greeting",
            "limit": 5,
        }
        resp = await client.post(url, headers=headers, json=payload)
        data = resp.json()
        print(
            f"Response ({resp.status_code}) - Total: {data.get('total')}, Count logic: {len(data.get('items', []))}"
        )

        print("\n--- Testing Filter by Status ---")
        payload = {"tenant_id": "demo-tenant", "status": "error", "limit": 5}
        resp = await client.post(url, headers=headers, json=payload)
        data = resp.json()
        print(
            f"Response ({resp.status_code}) - Total: {data.get('total')}, Status filtered items: {len(data.get('items', []))}"
        )


if __name__ == "__main__":
    asyncio.run(run_query_test())

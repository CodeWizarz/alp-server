import asyncio
import httpx


async def run_stats_test():
    base_url = "http://localhost:8000/v1/stats"
    headers = {
        "X-API-Key": "demo-key",
        "X-Tenant-ID": "demo-tenant",
    }

    async with httpx.AsyncClient() as client:
        print("\n--- Testing Error Stats ---")
        err_response = await client.get(f"{base_url}/errors", headers=headers)
        print(
            f"Error Stats Response ({err_response.status_code}): {err_response.json()}"
        )

        print("\n--- Testing Top Functions ---")
        top_response = await client.get(f"{base_url}/top-functions", headers=headers)
        print(
            f"Top Functions Response ({top_response.status_code}): {top_response.json()}"
        )


if __name__ == "__main__":
    asyncio.run(run_stats_test())

import asyncio
import httpx


async def run_auth_test():
    url = "http://localhost:8000/v1/test-auth"

    # Valid Request
    print("\n--- Testing Valid Headers ---")
    headers_valid = {
        "X-API-Key": "demo-key",
        "X-Tenant-ID": "demo-tenant",
    }
    async with httpx.AsyncClient() as client:
        valid_response = await client.get(url, headers=headers_valid)
        print(
            f"Valid Headers Response ({valid_response.status_code}): {valid_response.text}"
        )

    # Invalid Request (Wrong Key)
    print("\n--- Testing Invalid Key ---")
    headers_invalid = {
        "X-API-Key": "wrong-key",
        "X-Tenant-ID": "demo-tenant",
    }
    async with httpx.AsyncClient() as client:
        invalid_response = await client.get(url, headers=headers_invalid)
        print(
            f"Invalid Key Response ({invalid_response.status_code}): {invalid_response.text}"
        )

    # Health (Unauthenticated Endpoint)
    print("\n--- Testing Public Endpoint (/health) ---")
    async with httpx.AsyncClient() as client:
        health_response = await client.get("http://localhost:8000/health")
        print(
            f"Health Response ({health_response.status_code}): {health_response.text}"
        )


if __name__ == "__main__":
    asyncio.run(run_auth_test())

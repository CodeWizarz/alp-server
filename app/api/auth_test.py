from fastapi import APIRouter, Depends
from app.core.auth import verify_auth

router = APIRouter()


@router.get("/test-auth")
async def test_auth(tenant_id: str = Depends(verify_auth)):
    return {"message": "Authenticated", "tenant": tenant_id}

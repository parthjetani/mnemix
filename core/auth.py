import httpx
from fastapi import Header, HTTPException

from config import settings


async def get_current_user(authorization: str = Header(default=None)) -> dict:
    """Validate Supabase JWT by calling Supabase's /auth/v1/user endpoint."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error": "Missing or invalid Authorization header"})

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail={"error": "Empty token"})

    # Dev bypass, gated behind DEBUG so it can't fire in a deployed environment.
    if settings.DEBUG and token == "dev-local":
        return {"id": "dev-user", "email": "dev@localhost"}

    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=503,
            detail={"error": "Auth provider not configured"},
        )

    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": settings.SUPABASE_ANON_KEY,
            },
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})

    return resp.json()

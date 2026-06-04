from fastapi import APIRouter

router = APIRouter()


@router.get("/api/users/me")
async def me():
    return {"status": "not_implemented_yet"}

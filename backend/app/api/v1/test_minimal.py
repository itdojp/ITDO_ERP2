from fastapi import APIRouter

router = APIRouter()


@router.get("/test")
async def test_endpoint() -> None:
    return {"status": "working", "protocol": "v21.0"}

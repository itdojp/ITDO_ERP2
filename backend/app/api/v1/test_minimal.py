from fastapi import APIRouter

router = APIRouter()

<<<<<<< HEAD

@router.get("/test")
async def test_endpoint() -> None:
    return {"status": "working", "protocol": "v21.0"}
=======
@router.get("/test")
async def test_endpoint():
    return {"status": "working", "protocol": "v21.0"}
>>>>>>> origin/main

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_simple_health_check():
    """Test simple health check endpoint - practical version"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/simple/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ITDO ERP API"
    assert data["version"] == "v19.0-practical"
    assert data["mode"] == "working_over_perfect"
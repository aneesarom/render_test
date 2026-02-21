import uuid

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.auth.dependencies import get_current_user
from app.main import app
from app.auth.jwt_handler import create_access_token # For generating tokens for testing

client = TestClient(app)

# Integration test for /suggest API
def test_suggest_api_integration():
    mock_user = {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "is_admin": False
    }

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.post("/ai/suggest", json={"title": "Implement a new feature"})
    assert response.status_code == 200
    assert "task_description" in response.json()
    assert isinstance(response.json()["task_description"], list)
    app.dependency_overrides = {}

# Unit tests for users/me API (happy path)
def test_get_me_happy_path():

    mock_user = {
        "id": str(uuid.uuid4()),  # ✅ valid UUID
        "email": "test@example.com",
        "is_admin": False
    }

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get("/users/me")

    assert response.status_code == 200
    assert response.json() == mock_user

    app.dependency_overrides = {}

# Unit tests for tasks/update API (happy path)
@patch('app.supabase.supabase_client.supabase.table')
@patch('app.auth.dependencies.get_current_user')
def test_update_task_happy_path(mock_get_current_user, mock_supabase_table):
    mock_user = {"id": "test_user_id", "email": "test@example.com", "is_admin": False}
    mock_get_current_user.return_value = mock_user

    mock_updated_task_data = {
        "id": 1,
        "title": "Updated Task Title",
        "status": "in-progress",
        "description": "Updated description.",
        "total_minutes": 90.0
    }
    
    mock_execute = MagicMock()
    mock_execute.return_value.data = [mock_updated_task_data]
    mock_supabase_table.return_value.update.return_value.eq.return_value.execute = mock_execute

    task_id = 1
    update_payload = {
        "title": "Updated Task Title",
        "status": "in-progress",
        "description": "Updated description.",
        "total_minutes": 90.0
    }

    token = create_access_token(mock_user["id"])
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(f"/tasks/update/{task_id}", json=update_payload, headers=headers)

    assert response.status_code == 200
    assert response.json() == mock_updated_task_data

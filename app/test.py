import pytest
from fastapi.testclient import TestClient
from app.api.main import app  # Replace with your app name

client = TestClient(app)

def test_incorrectly_structured_data():
    response = client.post("/type", json={"incorrect": "data"})
    assert response.status_code == 400

def test_missing_fields():
    response = client.post("/type", json={"type": "Test", "assistant": "Assistant"})
    assert response.status_code == 400

def test_missing_parent():
    response = client.post("/type", json={"type": "NonExistentType", "assistant": "Assistant", "count": 5})
    assert response.status_code == 404

def test_duplicate_type():
    # First, create a type
    client.post("/type", json={"type": "Test", "assistant": "Assistant", "count": 5})
    
    # Then, try to create the same type again
    response = client.post("/type", json={"type": "Test", "assistant": "Assistant", "count": 5})
    assert response.status_code == 200  # This should still return 200, but the duplicate type should not be inserted again

def test_missing_assistant():
    response = client.post("/type", json={"type": "Test", "assistant": "NonExistentAssistant", "count": 5})
    assert response.status_code == 404

def test_invalid_count():
    response = client.post("/type", json={"type": "Test", "assistant": "Assistant", "count": -5})
    assert response.status_code == 400

def test_valid_request():
    response = client.post("/type", json={"type": "Test", "assistant": "Assistant", "count": 5})
    assert response.status_code == 200

def test_no_json_data():
    response = client.post("/type")
    assert response.status_code == 422

def test_count_over_maximum():
    response = client.post("/type", json={"type": "Test", "assistant": "Assistant", "count": 11})
    assert response.status_code == 400

def test_parent_children_count_over_limit():
    # First, create a type with 10 children
    for _ in range(10):
        client.post("/type", json={"type": "Test", "assistant": "Assistant", "count": 1})
    
    # Then, try to add another child to the same type
    response = client.post("/type", json={"type": "Test", "assistant": "Assistant", "count": 1})
    assert response.status_code == 400
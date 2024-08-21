from fastapi.testclient import TestClient
from main import app  # Replace 'your_app' with the name of your FastAPI app

client = TestClient(app)

def test_get_all_subtypes():
    response = client.get("/subtypes/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_subtype_by_type_success():
    response = client.get("/subtypes/orc")
    assert response.status_code == 200
    assert response.json()["type"] == "orc"

def test_get_subtype_by_type_failure():
    response = client.get("/subtypes/non_existent_type")
    assert response.status_code == 404

def test_get_subtype_children_success():
    response = client.get("/subtypes/children/orc")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_subtype_children_failure():
    response = client.get("/subtypes/children/non_existent_type")
    assert response.status_code == 404

def test_get_all_subtype_children():
    response = client.get("/subtypes/children/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_subtype_success():
    subtype = {"general_description": "Test", "physical_description": "Test", "type": "test_type"}
    response = client.post("/subtypes/", json=subtype)
    assert response.status_code == 200
    assert response.json()["type"] == "test_type"
    assert response.json()["children"] == []

def test_create_subtype_failure_existing_type():
    subtype = {"general_description": "Test", "physical_description": "Test", "type": "orc"}
    response = client.post("/subtypes/", json=subtype)
    assert response.status_code == 400
    assert response.json()["detail"] == "Subtype with this type already exists"

def test_create_subtype_failure_invalid_data():
    subtype = {"general_description": "Test", "physical_description": "Test"}
    response = client.post("/subtypes/", json=subtype)
    assert response.status_code == 422
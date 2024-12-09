from fastapi.testclient import TestClient
# Replace 'your_app' with the actual import path to your FastAPI app
from ..main import app

client = TestClient(app)


def test_token_creation_invalid_credentials():
    headers = {
        "client_id": "testing",
        "client_secret": "123456"
    }

    response = client.get("/pragya/token", headers=headers)

    assert response.status_code == 401
    assert response.json() == {
        "message": "Invalid client or secret ID", "type": "Error"}


def test_token_creation_valid_credentials():
    # Replace these with valid client_id and client_secret
    valid_client_id = "gridzydev"
    valid_client_secret = "5ebbbaf16f9ec96c2f56ef1e5d92ab6423af9f63eb567052fdb9806314c9c465"

    headers = {
        "client_id": valid_client_id,
        "client_secret": valid_client_secret
    }

    response = client.get("/pragya/token", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_create_nugget_valid_credentials():
    # Replace these with valid client_id and client_secret
    valid_client_id = "gridzydev"
    valid_client_secret = "5ebbbaf16f9ec96c2f56ef1e5d92ab6423af9f63eb567052fdb9806314c9c465"

    headers = {
        "client_id": valid_client_id,
        "client_secret": valid_client_secret
    }

    # Replace this with valid input data
    input_data = {
        "collection": "Testing",
        "card_title": "Testing",
        "frontend_id": "33",
        "technology": [
            "Testing"
        ],
        "context_background": "Testing",
        "functionality_in_scope": "Testing",
        "functionality_out_of_scope": "Testing",
        "artifact_tag": [
            "Testing"
        ],
        "knowledge_source": "Testing",
        "development_scope": "Testing",
        "lob": [
            "Testing"
        ],
        "system_demo": "",
        "system_demo_document_number": "",
        "demo_presentation_link": "https://Testing",
        "features_enabled": [
            ""
        ],
        "functional_specification_document_link": "https://Testing",
        "requirement_document_link": "",
        "technical_specification_document_link": "",
        "requested_by": "Testing",
        "requested_on": "07/13/2023 02:59:47",
        "status": "Testing",
        "approver": "SDSD Chhetri",
        "approver_remark": "looks good",
        "approved_or_rejected_on": "07/13/2023 07:16:25",
        "parent_nugget": "",
        "is_restricted_nugget": "True",
        "version": "1",
        "nugget_access_to": [
            "CEG1COB"
        ]
    }

    response = client.post("/create-nugget", json=input_data, headers=headers)

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert "nugget_id" in response.json()


def test_create_nugget_invalid_credentials():
    headers = {
        "client_id": "invalid_id",
        "client_secret": "invalid_secret"
    }

    # Replace this with valid input data
    input_data = {
        "key1": "value1",
        "key2": "value2",
        # ... other keys and values
    }

    response = client.post("/create-nugget", json=input_data, headers=headers)

    assert response.status_code == 401
    assert response.json() == {"message": "Unauthorized"}

# Add more test cases as needed to cover different scenarios

import pytest

from fastapi.testclient import TestClient
from main import app

from routers import subscriptions

client = TestClient(app=app)

@pytest.mark.integration
class TestCreateSubscription:
    def test_api_create_subscription_valid_input(self):
        response = client.post(
            "/v1/subscriptions",
            json={
                "url": "https://example.com/webhook",
                "event_types": ["stock.replenished"],
            }
        )

        assert response.status_code == 201

        data = response.json()
        assert "secret" in data
        assert data["secret"]

    def test_api_create_subscription_invalid_event(self):
        response = client.post(
                    "/v1/subscriptions",
                    json={
                        "url": "https://example.com/webhook",
                        "event_types": ["fake.event_type"],
                    }
                )

        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    @pytest.mark.integration
    def test_invalid_http(self):
        response = client.post(
                    "/v1/subscriptions",
                    json={
                        "url": "http://example.com/webhook",
                        "event_types": [""],
                    }
                )

        assert response.status_code == 422

@pytest.mark.integration
class TestGetSubscription:
    def test_existing_subscription_id(self):
        #create a subscription
        subscription_response = client.post(
            "/v1/subscriptions",
            json={
                "url": "https://example.com/webhook",
                "event_types": ["stock.replenished"]
            }
        )
        data_subscription = subscription_response.json()

        valid_url = f"/v1/subscriptions/{data_subscription["id"]}"
        response = client.get(valid_url)

        print(f"GET subscriptions: {response.json()}")

        assert response.status_code == 200
        #should not return secret key
        data = response.json()
        assert "secret" not in data

    def test_nonexistent_valid_uuid(self):
        response = client.get(
            "/v1/subscriptions/550e8400-e29b-41d4-a716-446655440000",
        )

        assert response.status_code == 404

    def test_malformed_uuid(self):
        response = client.get(
            "/v1/subscriptions/550e8400446655440000"
        )
        assert response.status_code == 422
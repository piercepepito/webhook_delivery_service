import pytest

from worker import tasks
from routers import subscriptions

import schemas

from main import app
from fastapi.testclient import TestClient
client = TestClient(app=app)

@pytest.mark.integration
def test_valid_input_data(clean_database, valid_subscription_payload):
    """
    Tests v1/events api using valid input data. Expected to have a 201 status code response
    """
    subscription_payload = schemas.subscriptions.SubscriptionCreate(**valid_subscription_payload[1])
    new_subscription = subscriptions.create_subscription(subscription_payload) 

    event_input = {
        "type": "asset.decommissioned",
        "occurred_at": "2026-09-18T06:00:00+08:00",
        "payload": {
            "lot_number": "CD-2026-0914",
            "sku": "BUTTER-UNSALTED-5KG",
            "expiry_date": "2026-09-25",
            "days_remaining": 7,
            "quantity": 24,
            "location": "COLD-02"
        }
    }

    response =client.post(
        "/v1/events",
        json=event_input
    )

    assert response.status_code == 201

@pytest.mark.integration
def test_invalid_input_data(clean_database, valid_subscription_payload):
    """
    Tests v1/events api using valid input data. Expected to have a 201 status code response
    """
    subscription_payload = schemas.subscriptions.SubscriptionCreate(**valid_subscription_payload[1])
    new_subscription = subscriptions.create_subscription(subscription_payload) 

    event_input = {
        "type": "asset.decommissioned",
        "payload": {
            "lot_number": "CD-2026-0914",
            "sku": "BUTTER-UNSALTED-5KG",
            "expiry_date": "2026-09-25",
            "days_remaining": 7,
            "quantity": 24,
            "location": "COLD-02"
        }
    }

    response = client.post(
        "/v1/events",
        json=event_input
    )

    assert response.status_code == 422
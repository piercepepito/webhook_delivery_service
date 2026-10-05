from routers import deliveries, subscriptions, events

import pytest

from uuid import uuid4

from main import app
from fastapi.testclient import TestClient
client = TestClient(app=app)

@pytest.mark.integration
class TestGetDelivery:
    def test_valid_input(self, valid_create_subscription_payload, valid_event_type):
        new_subscription = subscriptions.create_subscription(valid_create_subscription_payload)
        new_event = events.post_event_data(valid_event_type[0])
    
        delivery_payload = {
            "event_id": new_event.id,
            "subscription_id": new_subscription.id
            }
    
        new_delivery = deliveries.post_new_delivery(delivery_payload)

        delivery_url = f"/v1/deliveries/{str(new_delivery.id)}"
        response = client.get(delivery_url)
  
        assert response.status_code == 200

    def test_invalid_input(self):
        fake_uuid = str(uuid4())

        delivery_url = f"/v1/deliveries/{fake_uuid}"

        response = client.get(delivery_url)
        
        assert response.status_code == 404
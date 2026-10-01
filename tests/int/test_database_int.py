from database import delivery_and_attempts
from routers import deliveries, events, subscriptions

import pytest

@pytest.mark.integration
def test_database_delivery_and_delivery_attempt(valid_create_subscription_payload, valid_event_type): #valid_deliveries_payload
    """
    Focuses on the delivery_attempt_payload and should have the expected returned data

    Args:
    valid_deliveries_payload which contains the event id and subscription id
    """
    new_subscription = subscriptions.create_subscription(valid_create_subscription_payload)
    new_event = events.post_event_data(valid_event_type[0])

    delivery_payload = {
        "event_id": new_event.id,
        "subscription_id": new_subscription.id
    }

    delivery_data = deliveries.post_new_delivery(delivery_payload)

    delivery_attempt_payload_input = {
        "delivery_id":delivery_data.id,
        "attempt_no":delivery_data.attempt_count + 1,
        "status_code":200,
        "duration_ms":45
    }
    delivery_status = "pending"
    seconds = 37

    response = delivery_and_attempts.message_sent_attempt(delivery_attempt_payload_input,
                                                          delivery_status,
                                                          seconds)

    assert response["delivery_id"] == str(delivery_attempt_payload_input["delivery_id"])
    assert "status" in response
import pytest

from routers import deliveries, subscriptions, events

from sqlalchemy.exc import IntegrityError

from datetime import datetime

@pytest.mark.integration
def test_valid_delivery_payload(valid_create_subscription_payload, valid_event_type):
    new_subscription = subscriptions.create_subscription(valid_create_subscription_payload)
    new_event = events.post_event_data(valid_event_type[0])

    delivery_payload = {
        "event_id": new_event.id,
        "subscription_id": new_subscription.id
        }

    response = deliveries.post_new_delivery(delivery_payload)

    assert hasattr(response, "id") 
    assert hasattr(response, "event_id")
    assert hasattr(response, "subscription_id")
    assert hasattr(response, "status")
    assert hasattr(response, "attempt_count")

@pytest.mark.integration
def test_invalid_delivery_payload(valid_event_type):
    new_event = events.post_event_data(valid_event_type[0])

    delivery_payload = {
        "event_id": new_event.id,
        }

    with pytest.raises(IntegrityError) as e:
        deliveries.post_new_delivery(delivery_payload)


@pytest.mark.integration
def test_valid_patch_delivery_table(valid_create_subscription_payload, valid_event_type):
    """
    Ensures that the output of the patch_existing_delivery_id func is as expected

    Args:
    valid_deliveries_payload: a valid payload used for post_new_delivery func
    """
    new_subscription = subscriptions.create_subscription(valid_create_subscription_payload)
    new_event = events.post_event_data(valid_event_type[0])

    delivery_payload = {
        "event_id": new_event.id,
        "subscription_id": new_subscription.id
        }

    delivery_data = deliveries.post_new_delivery(delivery_payload)

    delivery_id = delivery_data.id
    attempt_no = delivery_data.attempt_count
    status = "succeeded"
    next_attempt_at = "2026-09-28 13:30:30+08:00"

    response = deliveries.patch_existing_delivery_id(delivery_id=delivery_id, 
                                                     new_status=status, 
                                                     new_attempt_count=attempt_no,
                                                     next_attempt_at = datetime.fromisoformat(next_attempt_at))

    assert response.attempt_count == attempt_no
    assert response.id == delivery_id
    assert response.status == status
    assert response.next_attempt_at == datetime.fromisoformat(next_attempt_at)

@pytest.mark.integration
def test_invalid_patch_delivery_table(valid_create_subscription_payload, valid_event_type):
    """
    Tests patch_existing_delivery_id using an invalid input

    Raises
    IntegrityError: due to an invalid input data, an integrity error should occur
    """
    new_subscription = subscriptions.create_subscription(valid_create_subscription_payload)
    new_event = events.post_event_data(valid_event_type[0])

    delivery_payload = {
        "event_id": new_event.id,
        "subscription_id": new_subscription.id
        }

    delivery_data = deliveries.post_new_delivery(delivery_payload)

    delivery_id = delivery_data.id
    attempt_no = 2
    status = "invalid status field"
    next_attempt_at = "2026-09-28 13:30:30+08:00"

    with pytest.raises(IntegrityError) as error:
        deliveries.patch_existing_delivery_id(delivery_id=delivery_id, 
                                              new_status=status, 
                                              new_attempt_count=attempt_no,
                                              next_attempt_at=next_attempt_at)
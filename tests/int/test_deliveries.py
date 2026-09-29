import pytest

from routers import deliveries

from sqlalchemy.exc import IntegrityError

from datetime import datetime

@pytest.mark.integration
def test_valid_delivery_payload(valid_deliveries_payload):
    response = deliveries.post_new_delivery(valid_deliveries_payload)

    assert response.id 
    assert response.event_id
    assert response.subscription_id
    assert response.status
    assert response.attempt_count

@pytest.mark.integration
def test_valid_patch_delivery_table(valid_deliveries_payload):
    delivery_data = deliveries.post_new_delivery(valid_deliveries_payload)

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
def test_invalid_patch_delivery_table():
    delivery_id = "e99838e3-21c0-4bf0-b173-7e74d0fbddaa"
    attempt_no = 2
    status = "invalid status field"

    with pytest.raises(IntegrityError) as error:
        deliveries.patch_existing_delivery_id(delivery_id=delivery_id, new_status=status, new_attempt_count=attempt_no)
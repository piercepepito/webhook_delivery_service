import pytest

from routers import deliveries

@pytest.mark.integration
def test_valid_delivery_payload(valid_deliveries_payload):
    response = deliveries.post_new_delivery(valid_deliveries_payload)

    assert response.id 
    assert response.event_id
    assert response.subscription_id
    assert response.status
    assert response.attempt_count
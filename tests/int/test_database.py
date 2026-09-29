from database import delivery_and_attempts
from routers import deliveries

import pytest

@pytest.mark.integration
def test_database_delivery_and_delivery_attempt(valid_deliveries_payload):
    delivery_data = deliveries.post_new_delivery(valid_deliveries_payload)

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

    assert response.id == delivery_attempt_payload_input["delivery_id"]
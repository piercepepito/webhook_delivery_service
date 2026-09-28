from database import delivery_and_attempts

import pytest

@pytest.mark.integration
def test_database_delivery_and_delivery_attempt():
    delivery_attempt_payload_input = {
        "delivery_id":"f177bcc1-f894-4d43-be3c-f2fa2066eb5a",
        "attempt_no":999,
        "status_code":200,
        "duration_ms":45
    }
    delivery_status = "pending"
    seconds = 37

    response = delivery_and_attempts.message_sent_attempt(delivery_attempt_payload_input,
                                                          delivery_status,
                                                          seconds)

    assert str(response.id) == delivery_attempt_payload_input["delivery_id"]
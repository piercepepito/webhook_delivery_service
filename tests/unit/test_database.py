from unittest.mock import Mock, patch

from database import delivery_and_attempts

@patch("database.delivery_and_attempts.deliveries")
@patch("database.delivery_and_attempts.delivery_attempts")
def test_valid_data_deliver_delivery(mock_delivery_attempt_new, mock_patch_delivery):
    """
    Validates message_sent_attempt using valid input data
    """
    deliver_attempt_mock_output = Mock()
    deliver_attempt_mock_output.delivery_id = "delivery_id"
    mock_delivery_attempt_new.create_new_delivery_attempt.return_value = deliver_attempt_mock_output

    delivery_mock_output_patch = Mock()
    delivery_mock_output_patch.id = "delivery_id"
    delivery_mock_output_patch.status = "pending" 
    mock_patch_delivery.patch_existing_delivery_id.return_value = delivery_mock_output_patch

    delivery_attempt_payload_input = {
        "delivery_id":"dsfsdfsd",
        "attempt_no":7,
        "duration_ms":32
    }

    response = delivery_and_attempts.message_sent_attempt(delivery_attempt_payload_input, "pending", 40)

    args, kwargs = mock_delivery_attempt_new.create_new_delivery_attempt.call_args
    assert args[0] == delivery_attempt_payload_input

    args, kwargs = mock_patch_delivery.patch_existing_delivery_id.call_args
    assert args[0] == "delivery_id"
    assert args[1] == "pending"
    assert args[2] == delivery_attempt_payload_input["attempt_no"]

    assert response["delivery_id"] == delivery_mock_output_patch.id
    assert response["status"] == delivery_mock_output_patch.status

    mock_patch_delivery.patch_existing_delivery_id.assert_called_once()
    mock_delivery_attempt_new.create_new_delivery_attempt.assert_called_once()
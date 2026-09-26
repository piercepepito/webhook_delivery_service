import pytest

from unittest.mock import Mock, patch

from worker import tasks

@patch("worker.tasks.deliveries.patch_existing_delivery_id")
@patch("worker.tasks.delivery_attempts.create_new_delivery_attempt")
@patch("worker.tasks.webhook.deliver_webhook")
def test_delivery_valid_payload(mock_webhook_delivery, mock_delivery_attempt_insert, mock_patch_delivery_row):

    webhook_output_mock = Mock()
    mock_webhook_delivery.return_value = webhook_output_mock, 423

    delivery_attempt_object_output_mock = Mock()
    mock_delivery_attempt_insert.return_value = delivery_attempt_object_output_mock

    patch_deliveries_mock = Mock()
    mock_patch_delivery_row.return_value = patch_deliveries_mock

    destination_url = "sample_url" 
    webhook_payload = {"name": "John"}
    delivery_response = Mock()
    delivery_response.id = 42
    delivery_response.event_id = "sample"

    response = tasks.delivery(destination_url, webhook_payload, delivery_response)

    args, kwargs = mock_delivery_attempt_insert.call_args
    assert args[0]["duration_ms"] == 423
    assert args[0]["delivery_id"] == 42

    mock_webhook_delivery.assert_called_once()
    mock_delivery_attempt_insert.assert_called_once()
    mock_patch_delivery_row.assert_called_once()

    assert response["delivery_id"] == 42
    assert response["event_id"] == "sample"
    assert response["status"] == "succeeded"
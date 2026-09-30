import pytest

from unittest.mock import Mock, patch

from worker import tasks

@patch("worker.tasks.deliveries.patch_existing_delivery_id")
@patch("worker.tasks.delivery_attempts.create_new_delivery_attempt")
@patch("worker.tasks.webhook.deliver_webhook")
def test_delivery_valid_payload(mock_webhook_delivery, mock_delivery_attempt_insert, mock_patch_delivery_row):
    """
    Verifies that a valid webhook delivery successfully processes the response,
    records the delivery attempt with its duration and delivery ID, updates the
    delivery record, and returns the expected delivery details and status.
    """
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

@patch("worker.tasks.delivery")
@patch("worker.tasks.deliveries.post_new_delivery")
@patch("worker.tasks.subscriptions.get_subscription_url")
@patch("worker.tasks.events.post_event_data")
def test_fan_out_valid_data(mock_post_event, mock_get_sub_url, mock_new_delivery, mock_deliver_message):
    """
    Verifies that fan_out creates an event, retrieves matching subscriptions,
    creates a delivery record for each subscription, and queues an individual
    delivery task for each destination.
    """
    sample_event_response = Mock()
    sample_event_response.id = "aaa"
    sample_event_response.type = "sample_event"
    mock_post_event.return_value = sample_event_response

    sample_sub_url_response_1 = Mock()
    sample_sub_url_response_1.id = "destination_id_1"
    sample_sub_url_response_1.url = "destination_url_1"

    sample_sub_url_response_2 = Mock()
    sample_sub_url_response_2.id = "destination_id_2"
    sample_sub_url_response_2.url = "destination_url_2"
    mock_get_sub_url.return_value = [sample_sub_url_response_1, sample_sub_url_response_2]

    sample_post_delivery = Mock()
    mock_new_delivery.return_value = sample_post_delivery

    mock_deliver_message.side_effect = [
        {"delivery_id": sample_sub_url_response_1.id , "event_id":sample_event_response.id, "status":"succeeded"},
        {"delivery_id": sample_sub_url_response_2.id, "event_id":sample_event_response.id, "status":"succeeded"}
    ]

    sample_payload_input = {
        "type": "stock.below_reorder_point",
        "occurred_at": "2026-09-18T09:14:22+08:00",
        "payload": {
            "sku": "FLOUR-BREAD-25KG",
            "item_name": "Bread Flour 25kg",
            "current_qty": 38,
            "reorder_point": 40,
            "unit": "bag",
            "location": "A-12-3"
        }
        }
    
    fan_out_response = tasks.fan_out(sample_payload_input)

    args, kwargs = mock_get_sub_url.call_args
    assert args[0] == sample_event_response.type

    assert mock_new_delivery.call_args_list[0].args[0] == {
        "event_id": "aaa",
        "subscription_id": "destination_id_1"
    }
    assert mock_new_delivery.call_args_list[1].args[0] == {
        "event_id":"aaa",
        "subscription_id":"destination_id_2"
    }

    mock_post_event.assert_called_once()
    mock_get_sub_url.assert_called_once()
    mock_new_delivery.call_count == len(mock_get_sub_url)
    mock_deliver_message.call_count == len(mock_get_sub_url)

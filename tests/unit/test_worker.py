import pytest

from unittest.mock import Mock, patch

from worker import tasks
import uuid

from unittest.mock import Mock, patch
import uuid


@patch("worker.tasks.delivery_and_attempts.message_sent_attempt")
@patch("worker.tasks.webhook.deliver_webhook")
def test_delivery_valid_payload(
    mock_webhook_delivery,
    mock_message_sent_attempt
):
    """
    Verifies that a successful webhook delivery:
    - calls deliver_webhook with the correct inputs
    - records the delivery attempt as succeeded
    - returns the result from message_sent_attempt
    """

    webhook_output_mock = Mock()
    webhook_output_mock.status_code = 200

    mock_webhook_delivery.return_value = (
        webhook_output_mock,
        423
    )

    expected_output = {
        "delivery_id": "some-id",
        "status": "succeeded"
    }

    mock_message_sent_attempt.return_value = expected_output

    delivery_id = uuid.uuid4()

    destination_url = "sample_url"
    webhook_payload = {"name": "John"}
    secret_key = "secret_key"

    response = tasks.delivery(
        destination_url,
        webhook_payload,
        delivery_id,
        secret_key
    )

    mock_webhook_delivery.assert_called_once_with(
        destination_url,
        webhook_payload,
        secret_key
    )

    mock_message_sent_attempt.assert_called_once()

    args, kwargs = mock_message_sent_attempt.call_args

    assert args[0] == {
        "delivery_id": str(delivery_id),
        "attempt_no": 1,
        "duration_ms": 423
    }

    assert args[1] == "succeeded"
    assert args[2] == 0

    assert response == expected_output


@patch("worker.tasks.delivery")
@patch("worker.tasks.deliveries.post_new_delivery")
@patch("worker.tasks.subscriptions.get_subscription_url")
@patch("worker.tasks.events.post_event_data")
def test_fan_out_valid_data(
    mock_post_event,
    mock_get_sub_url,
    mock_new_delivery,
    mock_deliver_message
):
    """
    Verifies that fan_out creates an event, retrieves matching subscriptions,
    creates a delivery record for each subscription, and queues an individual
    delivery task for each destination.
    """

    # -------------------------
    # Event mock
    # -------------------------
    sample_event_response = Mock()
    sample_event_response.id = "aaa"
    sample_event_response.type = "sample_event"

    mock_post_event.return_value = sample_event_response

    # -------------------------
    # Subscription mocks
    # -------------------------
    sample_sub_url_response_1 = Mock()
    sample_sub_url_response_1.id = "destination_id_1"
    sample_sub_url_response_1.url = "destination_url_1"

    sample_sub_url_response_2 = Mock()
    sample_sub_url_response_2.id = "destination_id_2"
    sample_sub_url_response_2.url = "destination_url_2"

    mock_get_sub_url.return_value = [
        sample_sub_url_response_1,
        sample_sub_url_response_2
    ]

    # -------------------------
    # Delivery record mock
    # -------------------------
    sample_post_delivery = Mock()
    sample_post_delivery.id = "delivery_id_1"

    mock_new_delivery.return_value = sample_post_delivery

    # -------------------------
    # Celery task mock
    # -------------------------
    sample_task = Mock()
    sample_task.id = "task_id_1"

    mock_deliver_message.delay.return_value = sample_task

    # -------------------------
    # fan_out input
    # -------------------------
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

    # -------------------------
    # Run function
    # -------------------------
    fan_out_response = tasks.fan_out(sample_payload_input)

    # -------------------------
    # Verify event creation
    # -------------------------
    mock_post_event.assert_called_once()

    # -------------------------
    # Verify subscription lookup
    # -------------------------
    mock_get_sub_url.assert_called_once()

    args, kwargs = mock_get_sub_url.call_args

    assert args[0] == sample_event_response.type

    # -------------------------
    # Verify delivery creation
    # -------------------------
    assert mock_new_delivery.call_count == len(mock_get_sub_url.return_value)

    assert mock_new_delivery.call_args_list[0].args[0] == {
        "event_id": "aaa",
        "subscription_id": "destination_id_1",
        "delivery_id": "delivery_id_1",
        "status": "pending",
        "task_id": "task_id_1"
    }

    assert mock_new_delivery.call_args_list[1].args[0] == {
        "event_id": "aaa",
        "subscription_id": "destination_id_2",
        "delivery_id": "delivery_id_1",
        "status": "pending",
        "task_id": "task_id_1"
    }
    assert mock_new_delivery.call_count == len(mock_get_sub_url.return_value)
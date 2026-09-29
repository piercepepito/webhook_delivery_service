import pytest

from routers import deliveries
from worker import tasks

@pytest.mark.integration
def test_delivery_valid_1st_attempt(valid_deliveries_payload):
    delivery_data = deliveries.post_new_delivery(valid_deliveries_payload)

    destination_url = "http://127.0.0.1:8000/webhook"
    webhook_payload = {
        "sku":"dssfdsf",
        "event_type":"stock.below_reorder_point"
    }
    secret = "some_secret_key"
    
    task_result = tasks.delivery.delay(destination_url,
                                      webhook_payload,
                                      str(delivery_data.id),
                                      secret)

    deliver_response = task_result.get(timeout=30)

    assert deliver_response["delivery_id"] == str(delivery_data.id)
    assert deliver_response["status"] == "succeeded"

@pytest.mark.integration
def test_delivery_within_retry(valid_deliveries_payload):
    delivery_data = deliveries.post_new_delivery(valid_deliveries_payload)

    destination_url = "http://127.0.0.1:8000/webhook/retry-test"
    webhook_payload = {
        "sku":"dssfdsf",
        "event_type":"stock.below_reorder_point"
    }
    secret = "some_secret_key"
    
    task_result = tasks.delivery.delay(destination_url,
                                      webhook_payload,
                                      str(delivery_data.id),
                                      secret)
    deliver_response = task_result.get(timeout=120)

    assert deliver_response["delivery_id"] == str(delivery_data.id)

@pytest.mark.integration
def test_all_failed(valid_deliveries_payload):
    delivery_data = deliveries.post_new_delivery(valid_deliveries_payload)
    
    destination_url = "http://127.0.0.1:8000/webhook/all-fail"
    webhook_payload = {
        "sku":"dssfdsf",
        "event_type":"stock.below_reorder_point"
    }
    secret = "some_secret_key"
    
    task_result = tasks.delivery.delay(destination_url,
                                        webhook_payload,
                                        str(delivery_data.id),
                                        secret)
    deliver_response = task_result.get(timeout=300)

    assert deliver_response["delivery_id"] == str(delivery_data.id)
    assert deliver_response["status"] == "exhausted"

@pytest.mark.integration
def test_slow_server_response(valid_deliveries_payload):
    delivery_data = deliveries.post_new_delivery(valid_deliveries_payload)
    
    destination_url = "http://127.0.0.1:8000/webhook/slow"
    webhook_payload = {
        "sku":"dssfdsf",
        "event_type":"stock.below_reorder_point"
    }
    secret = "some_secret_key"
    
    task_result = tasks.delivery.delay(destination_url,
                                        webhook_payload,
                                        str(delivery_data.id),
                                        secret)
    deliver_response = task_result.get(timeout=300)

    assert deliver_response["delivery_id"] == str(delivery_data.id)
    assert deliver_response["status"] == "exhausted"


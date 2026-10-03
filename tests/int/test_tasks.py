import pytest

from routers import deliveries, subscriptions, events
from worker import tasks

from tests import helpers

import schemas

@pytest.mark.integration
class TestDelivery:
    def test_delivery_valid_1st_attempt(self, valid_create_subscription_payload, valid_event_type):
        """
        Verifies that the delivery func would succesfully send the data without any retries

        Args:
        """
        new_subscription = subscriptions.create_subscription(valid_create_subscription_payload)
        new_event = events.post_event_data(valid_event_type[0])
    
        delivery_payload = {
            "event_id": new_event.id,
            "subscription_id": new_subscription.id
            }

        delivery_data = deliveries.post_new_delivery(delivery_payload)

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

    def test_delivery_within_retry(self, valid_create_subscription_payload, valid_event_type):
        """
        Verifies that delivery will succesfully createa delivery attempt n times, and updates the delivery row.
        
        Args:
        valid_deliveries_payload
        """
        new_subscription = subscriptions.create_subscription(valid_create_subscription_payload)
        new_event = events.post_event_data(valid_event_type[0])
    
        delivery_payload = {
            "event_id": new_event.id,
            "subscription_id": new_subscription.id
            }
        
        delivery_data = deliveries.post_new_delivery(delivery_payload)

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

    def test_all_failed(self, valid_create_subscription_payload, valid_event_type):
        """
        Verifies that the status of the delivery should be 'exhausted' and has reached max retries which
        should be shown as 6 as attempt no

        Args:
        """
        new_subscription = subscriptions.create_subscription(valid_create_subscription_payload)
        new_event = events.post_event_data(valid_event_type[0])
    
        delivery_payload = {
            "event_id": new_event.id,
            "subscription_id": new_subscription.id
            }
        
        delivery_data = deliveries.post_new_delivery(delivery_payload)
        
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

    def test_slow_server_response(self,valid_create_subscription_payload, valid_event_type):
        """
        When server is too slow to respond, then the webhook shouldn't be able to succesfully send the request
        and update the delivery row status as 'exhausted'
        """
        new_subscription = subscriptions.create_subscription(valid_create_subscription_payload)
        new_event = events.post_event_data(valid_event_type[0])
    
        delivery_payload = {
            "event_id": new_event.id,
            "subscription_id": new_subscription.id
            }
        delivery_data = deliveries.post_new_delivery(delivery_payload)
        
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

@pytest.mark.integration
class TestFanOut:
    def test_fan_out_single_subscription_match(self, clean_database, valid_subscription_payload): 
        """
        Verifies that fan_out creates a delivery for a single matching subscription
        and queues the webhook delivery task.
        """
        subscription_payload = schemas.subscriptions.SubscriptionCreate(**valid_subscription_payload[1])
        new_subscription = subscriptions.create_subscription(subscription_payload) 

        event_input = {
            "type": "asset.decommissioned",
            "occurred_at": "2026-09-18T06:00:00+08:00",
            "payload": {
                "lot_number": "CD-2026-0914",
                "sku": "BUTTER-UNSALTED-5KG",
                "expiry_date": "2026-09-25",
                "days_remaining": 7,
                "quantity": 24,
                "location": "COLD-02"
            }
        }

        task_result = tasks.fan_out.delay(event_input)
        response = task_result.get()
        for row in response:
            assert row["status"] == "pending" 

        subscription_exist = subscriptions.get_subscription_url("asset.decommissioned")
        assert len(subscription_exist) == 1

    def test_multiple_matching_subscriptions(self, clean_database, valid_subscription_payload):
        """
        Verifies that fan_out creates a delivery for multiple matching subscription
        and queues the webhook delivery task.
        """
        
        for subscription_payload in valid_subscription_payload:
            valid_sub_payload = schemas.subscriptions.SubscriptionCreate(**subscription_payload)
            _  = subscriptions.create_subscription(valid_sub_payload)
        
        event_input = {
            "type": "asset.serial_registered",
            "occurred_at": "2026-09-18T06:00:00+08:00",
            "payload": {
                "lot_number": "CD-2026-0914",
                "sku": "BUTTER-UNSALTED-5KG",
                "expiry_date": "2026-09-25",
                "days_remaining": 7,
                "quantity": 24,
                "location": "COLD-02"
            }
        }
        task_result = tasks.fan_out.delay(event_input)
        response = task_result.get()
        for row in response:
            assert row["status"] == "pending" 

        subscription_exist = subscriptions.get_subscription_url("asset.serial_registered")
        assert len(subscription_exist) == 2

    def test_no_matching_subscription(self, clean_database):
        """
        fan_out should raise an error when no matching subscription url is returned
        """
        event_input = {
                    "type": "shipment.dispatched",
                    "occurred_at": "2026-09-18T06:00:00+08:00",
                    "payload": {
                        "lot_number": "CD-2026-0914",
                        "sku": "BUTTER-UNSALTED-5KG",
                        "expiry_date": "2026-09-25",
                        "days_remaining": 7,
                        "quantity": 24,
                        "location": "COLD-02"
                    }
                }
        task_result = tasks.fan_out.delay(event_input)
        with pytest.raises(ValueError, match="Unable to find url destination from given event type") as e:
            task_result.get(propagate=True)

    def test_mixed_results(self, clean_database):
            """
            Creates 2 examples wherein 1 succeeds, and another fails. The celery task should show 1 exhausted an another 
            succeeded delivery rows.
            """
            mixed_sub_results= [
                {"url": "http://127.0.0.1:8000/webhook",
                "event_types": ["asset.serial_registered"]},
                {"url": "http://127.0.0.1:8000/webhook/all-fail",
                "event_types": ["asset.serial_registered", "asset.decommissioned"]},
            ]

            for subscription_payload in mixed_sub_results:
                    print(subscription_payload)
                    valid_sub_payload = schemas.subscriptions.SubscriptionCreate(**subscription_payload)
                    _  = subscriptions.create_subscription(valid_sub_payload)
                    
            event_input = {
                        "type": "asset.serial_registered",
                        "occurred_at": "2026-09-18T06:00:00+08:00",
                        "payload": {
                            "lot_number": "CD-2026-0914",
                            "sku": "BUTTER-UNSALTED-5KG",
                            "expiry_date": "2026-09-25",
                            "days_remaining": 7,
                            "quantity": 24,
                            "location": "COLD-02"
                        }
                    }
            task_result = tasks.fan_out.delay(event_input)
            response = task_result.get()

            results = helpers.wait_for_tasks([task_ids["task_id"] for task_ids in response])

            assert all(result.successful() for result in results)


            SUCCESS_URL = "http://127.0.0.1:8000/webhook" 
            
            for item in response:
                subscription_result = subscriptions.get_subscription(item["subscription_id"])
                delivery_data = deliveries.get_delivery(item["delivery_id"])

                expected_status =  "succeeded" if subscription_result.url == SUCCESS_URL else "exhausted"   

                assert delivery_data.status == expected_status


                 



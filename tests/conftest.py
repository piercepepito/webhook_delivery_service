import pytest

import random

@pytest.fixture
def valid_https_url():
    return ["https://subdomain.example.co.uk", "https://api.example.com/v1/subscriptions", 
            "https://example.com/path?key=value", "https://example.com/path/to/resource",
            "https://example.com?key=value"]

@pytest.fixture
def valid_https_url_prod():
    return ["https://subdomain.example.co.uk", "https://api.example.com/v1/subscriptions", 
            "https://example.com/path?key=value", "https://example.com/path/to/resource",
            "https://example.com?key=value"]

@pytest.fixture
def valid_https_url_dev():
    return ["https://subdomain.example.co.uk", "https://api.example.com/v1/subscriptions", 
            "https://example.com/path?key=value", "http://localhost:8000/docs", 
            "http://127.0.0.1:8000/docs"]

@pytest.fixture
def valid_event_types():
    return ["stock.replenished", "stock.adjusted_manually","lot.expiring_soon",
            "lot.expired","lot.quarantined"]

@pytest.fixture
def invalid_https_url():
    return ["http://localhost:8000/docs", "http://127.0.0.1:8000/docs", "http://localhost:8000",
            "https//example.com?key=value", "https://api.example.com/v1/subscriptions"]

@pytest.fixture
def invalid_event_types():
    return ["stock.replenifghshed", "stock.adjustd_manually","lot.expirrnig_soon",
            "lot.expdfgired","lot.quarertined"]

@pytest.fixture
def valid_type():
    """Used for events table. A valid event type"""
    return [
        {
        "type": "lot.expiring_soon",
        "occurred_at": "2026-09-18T06:00:00+08:00",
        "payload": {
            "lot_number": "CD-2026-0914",
            "sku": "BUTTER-UNSALTED-5KG",
            "expiry_date": "2026-09-25",
            "days_remaining": 7,
            "quantity": 24,
            "location": "COLD-02"
                }
        },
        {
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
    ]

@pytest.fixture
def invalid_type():
    """Used for events table. A INVALID event type"""
    return [
        {
        "type": "lot.expiring_soonest",
        "occurred_at": "2026-09-18T06:00:00+08:00",
        "payload": {
            "lot_number": "CD-2026-0914",
            "sku": "BUTTER-UNSALTED-5KG",
            "expiry_date": "2026-09-25",
            "days_remaining": 7,
            "quantity": 24,
            "location": "COLD-02"
                }
        },
        {
        "type": "stock.below_reorder_piont",
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
    ]

@pytest.fixture
def valid_deliveries_payload():
    return {
        "event_id":"f61b9712-bd9e-41c7-8f65-0163202c88f7",
        "subscription_id":"faac781f-d620-4ece-a8af-91d82c746659"
    }

@pytest.fixture
def valid_delivery_attempt_payload():
    random_duration = random.randint(5,25)
    random_attempt = random.randint(3, 10)

    return {
        "delivery_id":"e99838e3-21c0-4bf0-b173-7e74d0fbddaa",
        "duration_ms": random_duration,
        "attempt_no": random_attempt
    }

@pytest.fixture 
def invalid_delivery_attempt_payload():
    return {
        "delivery_id":"e99838e3-21c0-4bf0-b173-7e74d0fbddaa",
        "attempt_no":10,
        "duration_ms":27
    }
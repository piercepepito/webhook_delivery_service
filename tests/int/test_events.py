import pytest

from routers import events

@pytest.mark.integration
def test_create_event():
        sample_payload = {
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

        response = events.post_event_data(sample_payload)

        assert response.payload == sample_payload["payload"]
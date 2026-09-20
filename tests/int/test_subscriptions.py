import pytest

from routers import subscriptions

@pytest.mark.integration
def test_create_subscription():
    payload = {
        "url": "https://cascade.example.com/hooks/wms",
        "event_types": ["stock.below_reorder_point", "lot.expiring_soon"],
    }

    response = subscriptions.create_subscription(payload)

    expected = {
        "url":payload["url"],
        "event_types":payload["event_types"],
        "active":True
    }

    for key, values in expected.items():
        assert response[key] == values

    assert response["active"]
    assert response["id"]
    assert response["secret"]
    assert response["created_at"]
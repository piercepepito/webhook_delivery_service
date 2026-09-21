import pytest

from routers import subscriptions

from sqlalchemy.exc import NoResultFound, DataError

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

@pytest.mark.integration
def test_get_subscription_valid_uuid_in_db():
    """
    Tests if function can get the proper dataset from the id.
    Expected to only recieve a single row. 
    """
    response=subscriptions.get_subscription("faac781f-d620-4ece-a8af-91d82c746659")

    assert "id" in response
    assert "created_at" in response
    assert "event_types" in response
    assert "url" in response
    assert "active" in response
    assert "secret" not in response

def test_get_subscription_invalid_uuid():
    """
    from an invalid uuid input, a Dataerror should occur
    """
    with pytest.raises(ValueError) as error:
        subscriptions.get_subscription("faac781f-d620-4ece-a8af-91d82c746659-jdh")

    assert str(error.value) == "Improper UUID format"

def test_get_subscription_():
    """"""
    with pytest.raises(ValueError) as error:
        subscriptions.get_subscription("faac781f-d620-4ece-a8af-91d82c741111")

    assert str(error.value) == "No Id found from input"
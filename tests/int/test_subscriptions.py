import pytest

from routers import subscriptions

from sqlalchemy.exc import NoResultFound, DataError
from uuid import UUID
import schemas


@pytest.mark.integration
def test_create_subscription(valid_create_subscription_payload):
    payload = valid_create_subscription_payload

    response = subscriptions.create_subscription(payload)

    expected = {
        "url":str(payload.url),
        "event_types":payload.event_types,
        "active":True
    }

    for key, values in expected.items():
        assert getattr(response, key) == values

    assert hasattr(response, "secret")
    assert response.secret is not None
    assert response.secret != ""

@pytest.mark.integration
def test_get_subscription_valid_uuid_in_db(valid_create_subscription_payload):
    """
    Tests if function can get the proper dataset from the id.
    Expected to only recieve a single row. Internal usage only
    """
    payload = valid_create_subscription_payload
    new_subscription = subscriptions.create_subscription(payload)

    response=subscriptions.get_subscription(new_subscription.id)

    assert response.id == new_subscription.id
    assert hasattr(response, "secret")

@pytest.mark.integration
def test_get_subscription_invalid_uuid():
    """
    from an invalid uuid input, a Dataerror should occur
    """
    with pytest.raises(ValueError) as error:
        subscriptions.get_subscription("faac781f-d620-4ece-a8af-91d82c746659-jdh")

    assert str(error.value) == "Improper UUID format"

@pytest.mark.integration
def test_get_subscription_id_not_found():
    """a no result found error should occur from an id never found in the table"""
    with pytest.raises(ValueError) as error:
        subscriptions.get_subscription("faac781f-d620-4ece-1111-91d82c741111")

    assert str(error.value) == "No Id found from input"

@pytest.mark.integration
def test_get_subscription_url_invalid_type():
    """Running get_subscrition_url func with a type never found in the subscriptions table"""
    with pytest.raises(ValueError) as error:
        subscriptions.get_subscription_url("fake.event_no_exist")

    assert str(error.value) == "Unable to find url destination from given event type"

@pytest.mark.integration
def test_get_subscription_url_valid_type(valid_create_subscription_payload):
    """Running get_subscrition_url func with a type that exists in the subscriptio ns table"""
    payload = valid_create_subscription_payload
    new_subscription = subscriptions.create_subscription(payload)

    response = subscriptions.get_subscription_url(new_subscription.event_types[0])

    assert len(response) >= 1

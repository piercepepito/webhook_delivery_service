import pytest

from routers import subscriptions

from sqlalchemy.exc import NoResultFound, DataError
from uuid import UUID
import schemas

@pytest.mark.integration
class TestCreateSubscription:
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
class TestGetSubscription:
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

    def test_get_subscription_invalid_uuid():
        """
        from an invalid uuid input, a Dataerror should occur
        """
        with pytest.raises(ValueError) as error:
            subscriptions.get_subscription("faac781f-d620-4ece-a8af-91d82c746659-jdh")

        assert str(error.value) == "Improper UUID format"

    def test_get_subscription_id_not_found():
        """a no result found error should occur from an id never found in the table"""
        with pytest.raises(ValueError) as error:
            subscriptions.get_subscription("faac781f-d620-4ece-1111-91d82c741111")

        assert str(error.value) == "No Id found from input"

    def test_get_subscription_url_invalid_type():
        """Running get_subscrition_url func with a type never found in the subscriptions table"""
        with pytest.raises(ValueError) as error:
            subscriptions.get_subscription_url("fake.event_no_exist")

        assert str(error.value) == "Unable to find url destination from given event type"

@pytest.mark.integration
class TestSubscriptionUrl:
    def test_get_subscription_url_valid_type(valid_create_subscription_payload):
        """Running get_subscrition_url func with a type that exists in the subscriptio ns table"""
        payload = valid_create_subscription_payload
        new_subscription = subscriptions.create_subscription(payload)

        response = subscriptions.get_subscription_url(new_subscription.event_types[0])

        assert len(response) >= 1

@pytest.mark.integration
class TestUpdateSubscription:
    def test_patch_subscription_valid_input(self, valid_create_subscription_payload):    
        """
        Validates when all event and url are being added
        """
        payload = valid_create_subscription_payload
        new_subscription = subscriptions.create_subscription(payload)

        input_payload = {
                "event_types":["asset.serial_registered"],
                "url": "https://subdomain.example.co"
        }
        sub_update_payload = schemas.subscriptions.SubscriptionUpdate(**input_payload)

        response = subscriptions.update_subscription(new_subscription.id, sub_update_payload)

        assert response.event_types == input_payload["event_types"]
        assert response.url == input_payload["url"] + "/"

    def test_patch_subscription_missing_url(self, valid_create_subscription_payload):
        """
        Validates the output and checks that the url should not be changed
        """    
        payload = valid_create_subscription_payload
        new_subscription = subscriptions.create_subscription(payload)

        input_payload = {
            "event_types":["asset.serial_registered"]
        }
        sub_update_payload = schemas.subscriptions.SubscriptionUpdate(**input_payload)

        response = subscriptions.update_subscription(new_subscription.id, sub_update_payload)

        assert response.event_types == input_payload["event_types"]
        assert response.url == new_subscription.url

    def test_patch_subscription_missing_event(self, valid_create_subscription_payload):
        """
        Validates the output and checks that the url should not be changed
        """    
        payload = valid_create_subscription_payload
        new_subscription = subscriptions.create_subscription(payload)

        input_payload = {
            "url": "https://subdomain.example.co.uk"
        }
        sub_update_payload = schemas.subscriptions.SubscriptionUpdate(**input_payload)

        response = subscriptions.update_subscription(new_subscription.id, sub_update_payload)

        assert response.event_types == new_subscription.event_types
        assert response.url == input_payload["url"] + "/"

    def test_patch_empty_json(self, valid_create_subscription_payload):
        """
        Checks if an error will be raised if an empty json is being given
        """
        input_payload = {}
        with pytest.raises(ValueError) as e:
            schemas.subscriptions.SubscriptionUpdate(**input_payload)

            assert e == "At least one field must be provided"




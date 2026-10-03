import pytest 
from unittest.mock import patch

from schemas import subscriptions, events
from pydantic import ValidationError

class TestSubscriptionCreate:
    def test_valid_url_event_type_prod(self, valid_https_url_prod, valid_event_types, monkeypatch):
        """
        test for subscriptions schema for valid url running on prod
        """
        monkeypatch.setattr(subscriptions, "ENVIRONMENT", "production")
        for url, event_type in zip(valid_https_url_prod, valid_event_types):
            print(url, event_type)
            subscription_data = subscriptions.SubscriptionCreate(
                url=url, event_types=[event_type]
            )

            assert subscription_data.url.scheme == "https"
            assert subscription_data.event_types == [event_type]

    def test_valid_url_event_type_dev(self, valid_https_url_dev, valid_event_types, monkeypatch):
            """
            test for subscriptions schema for valid url running on dev
            """
            monkeypatch.setattr(subscriptions, "ENVIRONMENT", "development")
            for url, event_type in zip(valid_https_url_dev, valid_event_types):
                print(url, event_type)
                subscription_data = subscriptions.SubscriptionCreate(
                    url=url, event_types=[event_type]
                )

                assert subscription_data.event_types == [event_type]

    def test_invalid_url(self, invalid_https_url, valid_event_types):
        """
        test for subscription schema for invalid url
        """
        for url, event_type in zip(invalid_https_url, valid_event_types):
            with pytest.raises(ValidationError) as error:
                subscriptions.SubscriptionCreate(
                    url=url, event_types=event_type
                )

                assert str(error.value) == "HTTPS scheme is required"

    def test_invalid_event_types(self, valid_https_url, invalid_event_types):
        """
        test for subscription schema on invalid event types
        """
        for url, event_type in zip(valid_https_url, invalid_event_types):
            with pytest.raises(ValidationError) as error:
                subscriptions.SubscriptionCreate(
                    url=url, event_types=event_type
                )

                assert str(error.value) == f"The following events does not exist: {event_type}"

class TestEvents:
    def test_valid_type_validation(self, valid_event_type):
        for payload_event in valid_event_type:
            response = events.post_event_payload(**payload_event)

            assert str(response.type) == payload_event["type"]

    def test_invalid_type_validation(self, invalid_event_type):
        for payload_event in invalid_event_type:
            with pytest.raises(ValidationError) as error:
                response = events.post_event_payload(**payload_event)

                assert str(error.value) == f"{payload_event["type"]} not part of event catalog"


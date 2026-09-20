import pytest 
from unittest.mock import patch

from schemas import subscriptions
from pydantic import ValidationError

class TestSubscriptionCreate:
    def test_valid_url_event_type(self, valid_https_url, valid_event_types):
        for url, event_type in zip(valid_https_url, valid_event_types):
            print(url, event_type)
            subscription_data = subscriptions.SubscriptionCreate(
                url=url, event_types=[event_type]
            )

            assert subscription_data.url.scheme == "https"
            assert subscription_data.event_types == [event_type]

    def test_invalid_url(self, invalid_https_url, valid_event_types):
        for url, event_type in zip(invalid_https_url, valid_event_types):
            with pytest.raises(ValidationError) as error:
                subscriptions.SubscriptionCreate(
                    url=url, event_types=event_type
                )

                assert str(error.value) == "HTTPS scheme is required"

    def test_invalid_event_types(self, valid_https_url, invalid_event_types):
        for url, event_type in zip(valid_https_url, invalid_event_types):
            with pytest.raises(ValidationError) as error:
                subscriptions.SubscriptionCreate(
                    url=url, event_types=event_type
                )

                assert str(error.value) == f"The following events does not exist: {event_type}"


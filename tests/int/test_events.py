import pytest

from routers import events
from sqlalchemy.exc import IntegrityError

@pytest.mark.integration
def test_create_event(valid_type):
        response = events.post_event_data(valid_type[0])

        assert response.payload == valid_type[0]["payload"]

@pytest.mark.integration
def test_create_event_invalid_input(valid_type):
        """Purposefully sends incomplete data and should return an Integrity Error"""
        valid_type = valid_type[0]
        del valid_type["payload"]
        
        with pytest.raises(IntegrityError) as e:
            events.post_event_data(valid_type)
import pytest

from routers import delivery_attempts

from sqlalchemy.exc import IntegrityError

@pytest.mark.integration
def test_delivery_attempt_new_valid(valid_delivery_attempt_payload):
    """
    From a valid delivery payload, it checks for the proper output and no missing essential data is lost

    Args:
    valid_delivery_attempt_payload: a conftest fixture, a known valid input
    """
    response = delivery_attempts.create_new_delivery_attempt(valid_delivery_attempt_payload)

    assert response.id
    assert response.duration_ms == valid_delivery_attempt_payload["duration_ms"]
    assert response.attempt_no  == valid_delivery_attempt_payload["attempt_no"]
    assert str(response.delivery_id) == valid_delivery_attempt_payload["delivery_id"]

@pytest.mark.integration
def test_delivery_attempt_new_invalid(invalid_delivery_attempt_payload):
    """
    Checks for proper error handling, when an invalid input data is being sent

    Args:
    invalid_delivery_attempt_payload: an invalid input for the delivery function

    Raises:
    IntegrityError: raises when invalid input data is being added
    """
    with pytest.raises(IntegrityError) as error:
        delivery_attempts.create_new_delivery_attempt(invalid_delivery_attempt_payload)

@pytest.mark.integration
def test_delivery_attempt_new_with_error_code(valid_delivery_attempt_with_error_codes):
    """
    Ensures that for a retry, an error code should be seen when returned

    Args:
    valid_delivery_attempt_with_error_codes: input with error codes, status code, and error string
    """
    response = delivery_attempts.create_new_delivery_attempt(valid_delivery_attempt_with_error_codes)

    assert response.id
    assert response.duration_ms == valid_delivery_attempt_with_error_codes["duration_ms"]
    assert response.attempt_no  == valid_delivery_attempt_with_error_codes["attempt_no"]
    assert str(response.delivery_id) == valid_delivery_attempt_with_error_codes["delivery_id"]
    assert response.status_code == valid_delivery_attempt_with_error_codes["status_code"]
    assert response.error == valid_delivery_attempt_with_error_codes["error"]
    
from unittest.mock import Mock, patch

import pytest

from worker import webhook, exceptions
from requests import RequestException
import requests

@patch("worker.webhook.encryption")
@patch("worker.webhook.webhook_signature")
@patch("worker.webhook.requests")
def test_webhook_valid_payload(mock_requests, mock_signature, mock_encryption):
    """
    Verifies that a valid webhook response returns the HTTP response and the request
    duration in milliseconds
    """
    url = "https://sample.payload.com"
    payload = {
        "name": "John"
    }

    mock_signature.return_value = "hexadecimal_string"

    sample_output = Mock()
    mock_requests.post.return_value = sample_output

    sample_output.raise_for_status.return_value = None

    secret = "some_secret_key"
    mock_encryption.decrypt_keys.return_value = secret

    response = webhook.deliver_webhook(url, payload, secret)

    assert response[0] == sample_output
    assert response[1] > 0


@patch("worker.webhook.encryption")
@patch("worker.webhook.webhook_signature.generate_signature")
@patch("worker.webhook.requests.post")
def test_webhook_connection_error(mock_requests, mock_signature, mock_encryption):
        """
        Verifies that an error would occur, whenever there'e a failed connection
        """
        url = "https://sample.payload.com"
        payload = {
            "name": "John"
        }

        mock_signature.return_value = "hexadecimal_string"

        secret = "some_secret_key"
        mock_encryption.decrypt_keys.return_value = secret

        mock_requests.side_effect = requests.exceptions.ConnectionError(
        "Connection Failed")

        with pytest.raises(exceptions.WebDeliveryError):
            webhook.deliver_webhook(url, payload, secret)

        expected_headers = {
            "X-Webhook-Signature":"hexadecimal_string",
            "Content-Type":"application/json"
        }

        mock_requests.assert_called_once_with(url, 
                                              json=payload, 
                                              headers=expected_headers,
                                              timeout=(3,5))
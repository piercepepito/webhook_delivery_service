from unittest.mock import Mock, patch

import pytest

from worker import webhook
from requests import RequestException

@patch("worker.webhook.webhook_signature")
@patch("worker.webhook.requests")
def test_webhook_valid_payload(mock_requests, mock_signature):
    url = "https://sample.payload.com"
    payload = {
        "name": "John"
    }
    secret = "some_secret_key"

    mock_signature.return_value = "hexadecimal_string"

    sample_output = Mock()
    mock_requests.post.return_value = sample_output

    sample_output.raise_for_status.return_value = None

    response = webhook.deliver_webhook(url, payload, secret)

    assert response[0] == sample_output
    assert response[1] > 0

@patch("worker.webhook.webhook_signature")
@patch("worker.webhook.requests.post")
def test_webhook_connection_error(mock_requests, mock_signature):
        url = "https://sample.payload.com"
        payload = {
            "name": "John"
        }
        secret = "some_secret_key"

        mock_signature.return_value = "hexadecimal_string"

        sample_output = Mock()
        mock_requests.return_value = sample_output

        sample_output.raise_for_status.side_effect = RequestException("Connection Failed")

        with pytest.raises(RequestException):
            webhook.deliver_webhook(url, payload, secret)

        expected_headers = {
            "X-Webhook-Signature":"hexadecimal_string",
            "Content-Type":"application/json"
        }

        mock_requests.assert_called_once_with(url, payload, expected_headers)
from unittest.mock import Mock, patch

import pytest

from worker import webhook
from requests import RequestException

@patch("worker.webhook.requests")
def test_webhook_valid_payload(mock_requests):
    url = "https://sample.payload.com"
    payload = {
        "name": "John"
    }

    sample_output = Mock()
    mock_requests.post.return_value = sample_output

    sample_output.raise_for_status.return_value = None

    response = webhook.deliver_webhook(url, payload)

    assert response[0] == sample_output
    assert response[1] > 0

@patch("worker.webhook.requests.post")
def test_webhook_connection_error(mock_requests):
        url = "https://sample.payload.com"
        payload = {
            "name": "John"
        }

        sample_output = Mock()
        mock_requests.return_value = sample_output

        sample_output.raise_for_status.side_effect = RequestException("Connection Failed")

        with pytest.raises(RequestException):
            webhook.deliver_webhook(url, payload)

        mock_requests.assert_called_once_with(url, payload)
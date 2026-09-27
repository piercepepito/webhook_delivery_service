import requests
import time

from utils import webhook_signature

def deliver_webhook(url: str, webhook_payload: dict, secret_key: str) -> tuple[requests.Response, int]:
    """
    Delivers payload to the subscriber

    Args:
        url: the destination url of the subcriber
        webhook_payload: the data being sent
        secret key
    Returns:
        - the response of the POST request and
        - the duration of the function
    """
    signature = webhook_signature(secret_key, webhook_payload)

    headers = {
        "X-Webhook-Signature":signature,
        "Content-Type":"application/json"
    }

    start = time.perf_counter()
    try:
        response = requests.post(url, webhook_payload, headers)

        response.raise_for_status()
        end = time.perf_counter()
    except requests.RequestException as e:
        raise e

    duration_ms = (end-start)*1_000

    return response, duration_ms
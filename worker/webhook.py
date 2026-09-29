import requests
import time

from utils import webhook_signature
from worker import exceptions

def deliver_webhook(url: str, webhook_payload: dict, secret_key: str) -> tuple[requests.Response, float]:
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
    signature = webhook_signature.generate_signature(secret_key, webhook_payload)

    headers = {
        "X-Webhook-Signature":signature,
        "Content-Type":"application/json"
    }

    start = time.perf_counter()
    try:
        response = requests.post(url, 
                                 json = webhook_payload, 
                                 headers= headers,
                                 timeout=(3,5))

        response.raise_for_status()

        duration_ms = (time.perf_counter()-start)*1_000
        return response, duration_ms
    
    except requests.RequestException as e:
        duration_ms = (time.perf_counter()-start)*1_000
        raise exceptions.WebDeliveryError(e, duration_ms) from e
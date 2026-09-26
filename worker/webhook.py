import requests
import time

def deliver_webhook(url, webhook_payload):
    start = time.perf_counter()
    try:
        response = requests.post(url, webhook_payload)

        response.raise_for_status()
        end = time.perf_counter()
    except requests.RequestException as e:
        raise e

    duration_ms = (end-start)*1_000

    return response, duration_ms
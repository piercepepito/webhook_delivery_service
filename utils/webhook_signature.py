import hmac
import hashlib

import json

def generate_signature(secret: str, payload: dict) -> str:
    """
    Generates a signature from the secret and the payload
    Args:
        secret: the decoded secret key of the subscription
        payload: the data being sent to the subscriber
    Returns:
    a hexadecimal string to be used as a header when doing POST to the subscriber
    """
    secret_bytes = secret.encode("utf-8")

    payload_bytes = json.dumps(payload).encode("utf-8")

    signature = hmac.new(
        key=secret_bytes,
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    return signature
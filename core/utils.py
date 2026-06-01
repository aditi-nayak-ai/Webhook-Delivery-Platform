import hmac
import hashlib
import json


def generate_signature(secret: str, payload: dict) -> str:
    return hmac.new(
        key=secret.encode(),
        msg=json.dumps(payload, separators=(",", ":")).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

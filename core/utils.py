import hmac
import hashlib
import json
 
 
def generate_signature(secret: str, payload: dict) -> str:
    """
    Generate HMAC SHA256 signature for a webhook payload.
    Uses compact separators to produce a deterministic byte sequence.
    This is the single canonical implementation — import from here everywhere.
    """
    return hmac.new(
        key=secret.encode(),
        msg=json.dumps(payload, separators=(",", ":")).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
 

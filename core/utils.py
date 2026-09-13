import base64
import hashlib
import hmac
import json

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def generate_signature(secret: str, payload: dict) -> str:
    return hmac.new(
        key=secret.encode(),
        msg=json.dumps(payload, separators=(",", ":")).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()


def _get_fernet() -> Fernet:
    """
    Derive a Fernet key from SECRET_KEY so webhook secrets are encrypted at
    rest without requiring a second key to manage/rotate separately.
    A dedicated FIELD_ENCRYPTION_KEY env var overrides this if set, which
    is the recommended path for production (rotating SECRET_KEY would
    otherwise silently break decryption of every stored secret).
    """
    raw_key = getattr(settings, "FIELD_ENCRYPTION_KEY", None) or settings.SECRET_KEY
    digest = hashlib.sha256(raw_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError(
            "Could not decrypt webhook secret — FIELD_ENCRYPTION_KEY/SECRET_KEY "
            "does not match the key it was encrypted with."
        ) from exc

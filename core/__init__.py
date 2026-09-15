# Ensures core/celery.py (and its broker/result-backend config sourced from
# Django settings) is loaded as soon as Django imports this package —
# not just when the Celery worker CLI (`celery -A core worker`) starts it
# explicitly. Without this, `@shared_task`-decorated functions called from
# inside a Django request (e.g. `.delay()`) fall back to Celery's default,
# unconfigured app — which points at amqp://guest@localhost// instead of
# the real Redis broker, and connection attempts fail with
# ConnectionRefusedError.
from .celery import app as celery_app
 
__all__ = ("celery_app",)

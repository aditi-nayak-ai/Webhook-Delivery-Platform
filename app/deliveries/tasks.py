import logging

import requests
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction
from django.utils import timezone

from app.events.models import Event
from app.webhooks.models import Webhook
from core.utils import decrypt_secret, generate_signature

from .models import Delivery

logger = logging.getLogger(__name__)

# 4xx responses (other than 429, which signals "try again later") mean the
# request itself is malformed or unauthorized on the receiving end —
# retrying with the same payload will never succeed. Burning 3 retries
# and minutes of exponential backoff on a permanent failure just delays
# the "failed" status the caller needs to see and wastes worker capacity.
NON_RETRYABLE_STATUS_CODES = frozenset(range(400, 500)) - {408, 429}


@shared_task(bind=True, max_retries=3)
def send_webhook_task(self, webhook_id, event_id):
    try:
        webhook = Webhook.objects.get(id=webhook_id)
        event = Event.objects.get(id=event_id)
    except (Webhook.DoesNotExist, Event.DoesNotExist):
        # Referenced rows were deleted between .delay() and execution.
        # Nothing to retry — there's no webhook/event to deliver.
        logger.warning(
            "send_webhook_task skipped: webhook_id=%s event_id=%s no longer exists",
            webhook_id, event_id,
        )
        return

    # select_for_update inside an atomic block so two concurrent workers
    # picking up the same (webhook, event) pair can't both read
    # attempt_count=0 and both write attempt_count=1 — the second worker
    # blocks until the first commits, then sees the updated row.
    with transaction.atomic():
        delivery, _ = Delivery.objects.select_for_update().get_or_create(
            webhook=webhook,
            event=event,
        )
        delivery.attempt_count += 1
        delivery.save(update_fields=["attempt_count"])

    try:
        secret = decrypt_secret(webhook.secret)
        signature = generate_signature(secret, event.payload)

        response = requests.post(
            webhook.url,
            json=event.payload,
            headers={"X-Webhook-Signature": signature},
            timeout=5,
        )

        delivery.response_code = response.status_code
        delivery.response_body = response.text[:1000]
        response.raise_for_status()
        delivery.status = "success"

    except requests.exceptions.HTTPError as exc:
        delivery.status = "failed"
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code in NON_RETRYABLE_STATUS_CODES:
            logger.info(
                "Delivery %s got non-retryable status %s from %s — giving up.",
                delivery.id, status_code, webhook.url,
            )
        else:
            _safe_retry(self, delivery, exc)

    except Exception as exc:
        delivery.status = "failed"
        delivery.response_body = str(exc)[:1000]
        _safe_retry(self, delivery, exc)

    finally:
        delivery.last_attempt_at = timezone.now()
        delivery.save(update_fields=[
            "status", "response_code", "response_body", "last_attempt_at",
        ])


def _safe_retry(task, delivery, exc):
    """
    Wrap self.retry() so that once max_retries is exhausted we log and
    return instead of letting MaxRetriesExceededError blow past the
    finally block's status save and surface as an unhandled task failure
    in Celery/Sentry for something that is an expected terminal state.
    """
    try:
        raise task.retry(exc=exc, countdown=2 ** delivery.attempt_count)
    except MaxRetriesExceededError:
        logger.warning(
            "Delivery %s exhausted retries after %s attempts: %s",
            delivery.id, delivery.attempt_count, exc,
        )

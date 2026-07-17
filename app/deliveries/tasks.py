from celery import shared_task
from django.db import transaction
import requests
from django.utils import timezone
from app.webhooks.models import Webhook
from app.events.models import Event
from .models import Delivery
from core.utils import generate_signature


@shared_task(bind=True, max_retries=3)
def send_webhook_task(self, webhook_id, event_id):
    webhook = Webhook.objects.get(id=webhook_id)
    event = Event.objects.get(id=event_id)

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
        signature = generate_signature(webhook.secret, event.payload)

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
        raise self.retry(exc=exc, countdown=2 ** delivery.attempt_count)

    except Exception as exc:
        delivery.status = "failed"
        delivery.response_body = str(exc)
        raise self.retry(exc=exc, countdown=2 ** delivery.attempt_count)

    finally:
        delivery.last_attempt_at = timezone.now()
        delivery.save()

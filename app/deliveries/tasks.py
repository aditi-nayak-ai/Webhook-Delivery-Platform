from celery import shared_task
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

    delivery, _ = Delivery.objects.get_or_create(
        webhook=webhook,
        event=event,
    )

    delivery.attempt_count += 1

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

        # A 4xx/5xx is a failed delivery, not a successful one — without
        # this check every HTTP response (including 500s) was recorded as
        # "success" and the retry path never triggered for them.
        response.raise_for_status()

        delivery.status = "success"

    except requests.exceptions.HTTPError as exc:
        # response_code/response_body already captured above from the
        # actual server response — keep that instead of clobbering it
        # with the exception's string representation.
        delivery.status = "failed"
        raise self.retry(exc=exc, countdown=2 ** delivery.attempt_count)

    except Exception as exc:
        # Network-level failure (timeout, DNS, connection refused) — no
        # response object exists, so fall back to the exception text.
        delivery.status = "failed"
        delivery.response_body = str(exc)

        raise self.retry(exc=exc, countdown=2 ** delivery.attempt_count)

    finally:
        delivery.last_attempt_at = timezone.now()
        delivery.save()

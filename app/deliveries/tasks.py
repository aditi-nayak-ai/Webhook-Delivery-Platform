
from celery import shared_task
import requests
from django.utils import timezone
from app.webhooks.models import Webhook
from app.events.models import Event
from .models import Delivery
from core.utils import generate_signature  # single source of truth
 
 
@shared_task(bind=True, max_retries=3)
def send_webhook_task(self, webhook_id, event_id):
    webhook = Webhook.objects.get(id=webhook_id)
    event = Event.objects.get(id=event_id)
 
    delivery, _ = Delivery.objects.get_or_create(
        webhook=webhook,
        event=event,
    )
 
    # Increment attempt count on every attempt, not just failures.
    # This way the final record accurately reflects total attempts made,
    # whether the delivery ultimately succeeded or failed.
    delivery.attempt_count += 1
 
    try:
        signature = generate_signature(webhook.secret, event.payload)
 
        response = requests.post(
            webhook.url,
            json=event.payload,
            headers={"X-Webhook-Signature": signature},
            timeout=5,
        )
 
        delivery.status = "success"
        delivery.response_code = response.status_code
        delivery.response_body = response.text[:1000]  # guard against huge bodies
 
    except Exception as exc:
        delivery.status = "failed"
        delivery.response_body = str(exc)
 
        raise self.retry(exc=exc, countdown=2 ** delivery.attempt_count)
 
    finally:
        delivery.last_attempt_at = timezone.now()
        delivery.save()
 

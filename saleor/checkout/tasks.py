from datetime import timedelta

from celery.utils.log import get_task_logger
from django.db.models import Q
from django.utils import timezone

from ..celeryconf import app
from .models import Checkout

task_logger = get_task_logger(__name__)


@app.task
def delete_expired_checkouts():
    now = timezone.now()
    expired_anonymous_checkouts = Q(email__isnull=True) & Q(
        last_change__lt=now - timedelta(days=30)
    )
    expired_user_checkout = Q(email__isnull=False) & Q(
        last_change__lt=now - timedelta(days=90)
    )
    empty_checkouts = Q(lines__isnull=True) & Q(
        last_change__lt=now - timedelta(hours=6)
    )
    count, _ = Checkout.objects.filter(
        empty_checkouts | expired_anonymous_checkouts | expired_user_checkout
    ).delete()
    if count:
        task_logger.debug("Removed %s checkouts.", count)

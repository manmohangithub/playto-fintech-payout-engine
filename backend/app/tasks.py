from celery import shared_task
from django.db import transaction
from .models import Payout, Ledger
import time
import random

@shared_task(bind=True, max_retries=3)
def process_payout(self, payout_id):
    try:
        payout = Payout.objects.get(id=payout_id)

        if payout.status != "pending":
            return

        payout.status = "processing"
        payout.save()

        time.sleep(2)

        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout_id)

            if random.random() < 0.8:
                payout.status = "completed"
            else:
                payout.status = "failed"
                payout.retries += 1

                # refund on failure
                Ledger.objects.create(
                    merchant=payout.merchant,
                    amount=payout.amount,
                    type="credit"
                )

            payout.save()

    except Exception as e:
        raise self.retry(exc=e, countdown=2**self.request.retries)
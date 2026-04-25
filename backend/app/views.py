import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from .models import Merchant, Ledger, Payout, Idempotency
from .utils import get_balance
from .tasks import process_payout


# 🔹 BALANCE
def balance(request, mid):
    merchant = Merchant.objects.get(id=mid)
    return JsonResponse({
        "balance": get_balance(merchant)
    })


# 🔹 LIST PAYOUTS
def payouts_list(request, mid):
    merchant = Merchant.objects.get(id=mid)

    payouts = Payout.objects.filter(
        merchant=merchant
    ).order_by("-id")

    data = [
        {
            "id": p.id,
            "amount": p.amount,
            "status": p.status,
            "retries": p.retries
        }
        for p in payouts
    ]

    return JsonResponse({"data": data})


# 🔥 CREATE PAYOUT (IMPORTANT)
@csrf_exempt
def payout(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "invalid_method"}, status=405)

        body = json.loads(request.body)

        key = request.headers.get("Idempotency-Key")
        merchant = Merchant.objects.get(id=body["merchant_id"])
        amount = int(body["amount"])

        # 🔥 IDEMPOTENCY
        existing = Idempotency.objects.filter(key=key).first()
        if existing:
            return JsonResponse(json.loads(existing.response))

        with transaction.atomic():
            merchant = Merchant.objects.select_for_update().get(id=merchant.id)

            # 🔥 BALANCE CHECK
            if get_balance(merchant) < amount:
                return JsonResponse(
                    {"error": "insufficient_funds"},
                    status=400
                )

            # 🔥 DEBIT
            Ledger.objects.create(
                merchant=merchant,
                amount=amount,
                type="debit"
            )

            # 🔥 CREATE PAYOUT
            payout = Payout.objects.create(
                merchant=merchant,
                amount=amount,
                status="pending"
            )

            response = {"status": "pending"}

            Idempotency.objects.create(
                merchant=merchant,
                key=key,
                response=json.dumps(response)
            )

        # 🔥 ASYNC TASK
        process_payout.delay(payout.id)

        return JsonResponse(response)

    except Exception as e:
        print("ERROR:", str(e))  # 🔥 DEBUG PRINT
        return JsonResponse({"error": "server_error"}, status=500)
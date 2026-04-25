import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models, transaction
from .models import Merchant, Ledger, Payout, Idempotency


# -------- BALANCE --------
def balance(request, merchant_id):
    merchant = Merchant.objects.get(id=merchant_id)

    credits = Ledger.objects.filter(
        merchant=merchant, type="credit"
    ).aggregate(total=models.Sum("amount"))["total"] or 0

    debits = Ledger.objects.filter(
        merchant=merchant, type="debit"
    ).aggregate(total=models.Sum("amount"))["total"] or 0

    return JsonResponse({"balance": credits - debits})


# -------- PAYOUT LIST --------
def payouts(request, merchant_id):
    merchant = Merchant.objects.get(id=merchant_id)

    data = list(
        Payout.objects.filter(merchant=merchant)
        .order_by("-id")
        .values("id", "amount", "status", "retries")
    )

    return JsonResponse({"data": data})


# -------- PAYOUT --------
@csrf_exempt
def payout(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)

    try:
        data = json.loads(request.body)

        merchant_id = data.get("merchant_id")
        amount = data.get("amount")
        idem_key = request.headers.get("Idempotency-Key")

        if not merchant_id or amount is None or not idem_key:
            return JsonResponse({"error": "missing_fields"}, status=400)

        amount = int(amount)

        if Idempotency.objects.filter(key=idem_key).exists():
            return JsonResponse({"status": "duplicate"})

        with transaction.atomic():
            merchant = Merchant.objects.select_for_update().get(id=merchant_id)

            credits = Ledger.objects.filter(
                merchant=merchant, type="credit"
            ).aggregate(total=models.Sum("amount"))["total"] or 0

            debits = Ledger.objects.filter(
                merchant=merchant, type="debit"
            ).aggregate(total=models.Sum("amount"))["total"] or 0

            balance = credits - debits

            if balance < amount:
                return JsonResponse({"error": "insufficient_funds"}, status=400)

            Payout.objects.create(
                merchant=merchant,
                amount=amount,
                status="completed",
                retries=0
            )

            Ledger.objects.create(
                merchant=merchant,
                amount=amount,
                type="debit"
            )

            Idempotency.objects.create(key=idem_key)

        return JsonResponse({"status": "completed"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
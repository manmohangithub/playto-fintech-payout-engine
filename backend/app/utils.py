from django.db.models import Sum
from .models import Ledger

def get_balance(merchant):
    credit = Ledger.objects.filter(
        merchant=merchant, type='credit'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    debit = Ledger.objects.filter(
        merchant=merchant, type='debit'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return credit - debit
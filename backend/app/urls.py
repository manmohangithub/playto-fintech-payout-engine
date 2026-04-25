from django.urls import path
from .views import balance, payout, payouts_list

urlpatterns = [
    path('balance/<int:mid>/', balance),
    path('payout/', payout),
    path('payouts/<int:mid>/', payouts_list),
]
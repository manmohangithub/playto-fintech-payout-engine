from django.urls import path
from .views import balance, payout, payouts

urlpatterns = [
    path("balance/<int:merchant_id>/", balance),
    path("payouts/<int:merchant_id>/", payouts),
    path("payout/", payout),
]
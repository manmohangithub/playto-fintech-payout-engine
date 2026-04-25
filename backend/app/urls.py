
from django.urls import path
from .views import home, balance, payouts, payout

urlpatterns = [
    path("", home),
    path("balance/<int:merchant_id>/", balance),
    path("payouts/<int:merchant_id>/", payouts),
    path("payout/", payout),
]

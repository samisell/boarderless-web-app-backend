from django.urls import path
from .views import (
    WalletView, 
    TransactionListView, 
    InitializePaymentView, 
    VerifyPaymentView,
    InitializeFlutterwavePaymentView,
    VerifyFlutterwavePaymentView,
    UnitListView,
    UnitPurchaseView,
    UseUnitView
)

urlpatterns = [
    path('wallet/', WalletView.as_view(), name='user-wallet'),
    path('transactions/', TransactionListView.as_view(), name='user-transactions'),
    path('paystack/initialize/', InitializePaymentView.as_view(), name='paystack-initialize'),
    path('paystack/verify/', VerifyPaymentView.as_view(), name='paystack-verify'),
    path('flutterwave/initialize/', InitializeFlutterwavePaymentView.as_view(), name='flutterwave-initialize'),
    path('flutterwave/verify/', VerifyFlutterwavePaymentView.as_view(), name='flutterwave-verify'),
    path('units/', UnitListView.as_view(), name='unit-list'),
    path('units/purchase/', UnitPurchaseView.as_view(), name='unit-purchase'),
    path('units/use/', UseUnitView.as_view(), name='use-unit'),
]
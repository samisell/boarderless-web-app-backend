from django.urls import path
from .views import (
    AdminLoginView, 
    logout_view,
    dashboard,
    UserListView,
    TransactionListView,
    CountryListView,
    CountryCreateView,
    CountryUpdateView,
    CountryDeleteView,
    TwilioNumberListView,
    ReferralListView,
    UnitPurchaseListView,
    UnitUsageListView,
    SystemSettingsView
)

app_name = 'admin_dashboard'

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('', dashboard, name='dashboard'),

    # User Management URLs
    path('users/', UserListView.as_view(), name='user_list'),
    # path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'), # Placeholder

    # Payment & Transaction URLs
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),

    path('twilio-numbers/', TwilioNumberListView.as_view(), name='twilio_number_list'),

    path('referrals/', ReferralListView.as_view(), name='referral_list'),

    path('unit-purchases/', UnitPurchaseListView.as_view(), name='unit_purchase_list'),

    path('unit-usage/', UnitUsageListView.as_view(), name='unit_usage_list'),

    path('system-settings/', SystemSettingsView.as_view(), name='system-settings'),

    path('countries/', CountryListView.as_view(), name='country_list'),
    path('countries/add/', CountryCreateView.as_view(), name='country_add'),
    path('countries/<int:pk>/update/', CountryUpdateView.as_view(), name='country_update'),
    path('countries/<int:pk>/delete/', CountryDeleteView.as_view(), name='country_delete'),
]
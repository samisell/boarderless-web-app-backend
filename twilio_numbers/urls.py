from django.urls import path
from .views import (
    CountryListView, SearchNumberView, PurchaseNumberView, UserNumbersView, 
    ResubscribeNumberView, MakeCallView, VoiceCallbackView, IncomingCallView, SendSMSView, IncomingSMSView, CallStatusView, InboundCallStatusView, CallHistoryView, ConversationListView
)

urlpatterns = [
    path('countries/', CountryListView.as_view(), name='country-list'),
    path('search/', SearchNumberView.as_view(), name='search-number'),
    path('purchase/', PurchaseNumberView.as_view(), name='purchase-number'),
    path('my-numbers/', UserNumbersView.as_view(), name='my-numbers'),
    path('resubscribe/<int:pk>/', ResubscribeNumberView.as_view(), name='resubscribe-number'),
    path('make-call/', MakeCallView.as_view(), name='make-call'),
    path('incoming-call/', IncomingCallView.as_view(), name='incoming-call'),
    
    path('send-sms/', SendSMSView.as_view(), name='send-sms'),
    path('incoming-sms/', IncomingSMSView.as_view(), name='incoming-sms'),
    path('call-status/', CallStatusView.as_view(), name='call-status'),
    path('inbound-call-status/', InboundCallStatusView.as_view(), name='inbound-call-status'),
    path('calls/', CallHistoryView.as_view(), name='call-history'),
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    # path('conversations/', ConversationListView.as_view(), name='conversation-list'),
]
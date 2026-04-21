from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (ChangePasswordView, EmailVerificationView, LoginView,
                    LogoutView, ResendOTPView, SendOTPView,
                    PasswordResetConfirmView, PasswordResetRequestView,
                    UserProfileView, UserRegistrationView, DashboardDataView)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('activities/', DashboardDataView.as_view(), name='user-activities'),
]
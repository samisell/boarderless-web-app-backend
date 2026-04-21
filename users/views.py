import random
from datetime import datetime
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from payments.models import Wallet, Transaction
from twilio_numbers.models import TwilioNumber, Call, Message
from payments.serializers import TransactionSerializer

from .serializers import (ChangePasswordSerializer, EmailVerificationSerializer, UserProfileSerializer,
                          PasswordResetConfirmSerializer,
                          PasswordResetRequestSerializer, 
                          UserRegistrationSerializer)

User = get_user_model()


def generate_otp():
    return str(random.randint(100000, 999999))


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()
        current_year = datetime.now().year

        # Send Welcome Email
        welcome_subject = 'Welcome to Borderless!'
        welcome_context = {
            'username': user.username,
            'login_url': 'https://boarderlessnetwork.com/login', # Replace with your actual frontend login URL
            'year': current_year,
        }
        welcome_html_message = render_to_string('users/welcome_email.html', welcome_context)
        welcome_plain_message = render_to_string('users/welcome_email.txt', welcome_context) # Create a plain text version later

        welcome_email = EmailMultiAlternatives(
            welcome_subject,
            welcome_plain_message,
            settings.EMAIL_HOST_USER,
            [user.email]
        )
        welcome_email.attach_alternative(welcome_html_message, "text/html")
        welcome_email.send(fail_silently=False)

        # Send OTP Email
        otp_subject = 'Your One-Time Password (OTP) for Borderless'
        otp_context = {'otp': otp, 'year': current_year}
        otp_html_message = render_to_string('users/otp_email.html', otp_context)
        otp_plain_message = render_to_string('users/otp_email.txt', otp_context) # Create a plain text version later

        otp_email = EmailMultiAlternatives(
            otp_subject,
            otp_plain_message,
            settings.EMAIL_HOST_USER,
            [user.email])
        otp_email.attach_alternative(otp_html_message, "text/html")
        otp_email.send(fail_silently=False)


class EmailVerificationView(APIView):
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            try:
                user = User.objects.get(email=email)
                if user.otp == otp and user.is_otp_valid():
                    user.is_active = True
                    user.otp = None
                    user.otp_created_at = None
                    user.save()
                    return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)
                return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                if user.is_active:
                    return Response({'error': 'This account is already active.'}, status=status.HTTP_400_BAD_REQUEST)

                # Generate and save new OTP
                otp = generate_otp()
                user.otp = otp
                user.otp_created_at = timezone.now()
                user.save()

                # Send new OTP email
                otp_subject = 'Your New One-Time Password (OTP) for Borderless'
                otp_context = {'otp': otp, 'year': datetime.now().year}
                otp_html_message = render_to_string('users/otp_email.html', otp_context)
                otp_plain_message = render_to_string('users/otp_email.txt', otp_context)

                otp_email = EmailMultiAlternatives(otp_subject, otp_plain_message, settings.EMAIL_HOST_USER, [user.email])
                otp_email.attach_alternative(otp_html_message, "text/html")
                otp_email.send(fail_silently=False)

                return Response({'message': 'A new OTP has been sent to your email.'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                otp = generate_otp()
                user.otp = otp
                user.otp_created_at = timezone.now()
                user.save()
                current_year = datetime.now().year

                # Send OTP Email for password reset
                otp_subject = 'Your Password Reset OTP for Borderless'
                otp_context = {'otp': otp, 'year': current_year}
                otp_html_message = render_to_string('users/otp_email.html', otp_context)
                otp_plain_message = render_to_string('users/otp_email.txt', otp_context) # Create a plain text version later

                otp_email = EmailMultiAlternatives(
                    otp_subject,
                    otp_plain_message,
                    settings.EMAIL_HOST_USER,
                    [user.email]
                )
                otp_email.attach_alternative(otp_html_message, "text/html")
                otp_email.send(fail_silently=False)
                return Response({'message': 'Password reset OTP sent.'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                # Still return OK to not reveal if a user exists
                return Response({'message': 'If an account with this email exists, an OTP has been sent.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']

            try:
                user = User.objects.get(email=email)
                if user.otp == otp and user.is_otp_valid():
                    user.set_password(new_password)
                    user.otp = None
                    user.otp_created_at = None
                    user.save()
                    return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
                return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = User.objects.filter(email=email).first()

        if user and user.check_password(password):
            if user.is_active:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            return Response({'error': 'Account not activated.'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()

            # Prevent user from being logged out
            update_session_auth_hash(request, self.object)

            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from twilio.rest import Client
from twilio_numbers.models import TwilioNumber

class SendOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.phone_number:
            return Response({'error': 'You must have a verified phone number to receive an OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        # Find an active Twilio number owned by the user
        twilio_number = TwilioNumber.objects.filter(user=user, subscription_status='active').first()
        if not twilio_number:
            return Response({'error': 'You do not have an active Twilio number to send the OTP from.'}, status=status.HTTP_400_BAD_REQUEST)

        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                to=user.phone_number,
                from_=twilio_number.phone_number,
                body=f'Your OTP is: {otp}'
            )
            return Response({'message': 'OTP sent successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Twilio API error while sending OTP: {e}")
            return Response({'error': 'Failed to send OTP.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class DashboardDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Wallet and Transaction data
        wallet = Wallet.objects.filter(user=user).first()
        transactions = Transaction.objects.filter(wallet=wallet).order_by('-timestamp')[:10]
        
        # Twilio data
        active_numbers = TwilioNumber.objects.filter(user=user, subscription_status='active').count()
        total_calls = Call.objects.filter(user=user).count()
        unread_messages = Message.objects.filter(user=user, is_read=False).count()

        # Serialize data
        transaction_serializer = TransactionSerializer(transactions, many=True)

        return Response({
            'wallet_balance': wallet.balance if wallet else 0,
            'recent_transactions': transaction_serializer.data,
            'active_numbers': active_numbers,
            'total_calls': total_calls,
            'unread_messages': unread_messages
        })
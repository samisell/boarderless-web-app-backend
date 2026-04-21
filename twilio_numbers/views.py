from django.conf import settings
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from twilio.rest import Client
from .models import TwilioNumber, Country, TwilioNumberPrice, ServiceRate, Call, Message
from .serializers import TwilioNumberSerializer, CountrySerializer, CallSerializer, ConversationSerializer
from payments.models import Wallet
from django.utils import timezone
import datetime

class CountryListView(generics.ListAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated]

import logging

logger = logging.getLogger(__name__)

class SearchNumberView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        country_code = request.query_params.get('country_code', 'US')
        price_obj = TwilioNumberPrice.objects.first()
        price = price_obj.price if price_obj else 1000.00
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            available_numbers = client.available_phone_numbers(country_code).mobile.list(limit=10)
            
            response_data = [
                {
                    'phone_number': number.phone_number,
                    'friendly_name': number.friendly_name,
                    'locality': number.locality,
                    'price': price
                }
                for number in available_numbers
            ]
            return Response(response_data)
        except Exception as e:
            logger.error(f"Twilio API error while searching for numbers: {e}")
            return Response({'error': 'Failed to find available numbers. Please check the server logs for more details.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PurchaseNumberView(generics.CreateAPIView):
    serializer_class = TwilioNumberSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        phone_number_to_purchase = request.data.get('phone_number')
        bundle_sid = request.user.bundle_sid or request.data.get('bundle_sid')
        if not phone_number_to_purchase:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            months = int(request.data.get('months', 1))
            if months not in [1, 3, 6, 12]:
                return Response({'error': 'Invalid subscription duration. Valid options are 1, 3, 6, or 12 months.'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid months format.'}, status=status.HTTP_400_BAD_REQUEST)

        price_obj = TwilioNumberPrice.objects.first()
        monthly_price = price_obj.price if price_obj else 1000.00
        total_price = monthly_price * months

        wallet = Wallet.objects.get(user=request.user)
        if wallet.balance < total_price:
            return Response({'error': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            purchase_args = {
                'phone_number': phone_number_to_purchase,
                'voice_url': request.build_absolute_uri('/api/twilio/incoming-call/'),
                'voice_method': 'POST',
                'status_callback': request.build_absolute_uri(f'/api/twilio/inbound-call-status/?twilio_number={phone_number_to_purchase}'),
                'status_callback_method': 'POST',
                'sms_url': request.build_absolute_uri('/api/twilio/incoming-sms/'),
                'sms_method': 'POST'
            }
            if bundle_sid:
                purchase_args['bundle_sid'] = bundle_sid

            purchased_number = client.incoming_phone_numbers.create(**purchase_args)

            twilio_number = TwilioNumber.objects.create(
                user=request.user,
                sid=purchased_number.sid,
                phone_number=purchased_number.phone_number,
                friendly_name=purchased_number.friendly_name,
                price=total_price,
                subscription_end_date=timezone.now() + datetime.timedelta(days=30 * months)
            )
            
            wallet.balance -= total_price
            wallet.save()

            serializer = self.get_serializer(twilio_number)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserNumbersView(generics.ListAPIView):
    serializer_class = TwilioNumberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TwilioNumber.objects.filter(user=self.request.user, subscription_status='active')

class ResubscribeNumberView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        number = TwilioNumber.objects.get(pk=self.kwargs['pk'], user=request.user)
        if number.subscription_status == 'active':
            return Response({'error': 'This number is already active.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            months = int(request.data.get('months', 1))
            if months not in [1, 3, 6, 12]:
                return Response({'error': 'Invalid subscription duration. Valid options are 1, 3, 6, or 12 months.'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid months format.'}, status=status.HTTP_400_BAD_REQUEST)

        price_obj = TwilioNumberPrice.objects.first()
        monthly_price = price_obj.price if price_obj else 1000.00
        total_price = monthly_price * months

        wallet = Wallet.objects.get(user=request.user)
        if wallet.balance < total_price:
            return Response({'error': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

        wallet.balance -= total_price
        wallet.save()

        number.subscription_status = 'active'
        number.subscription_end_date = timezone.now() + datetime.timedelta(days=30 * months)
        number.save()

        return Response({'success': 'Number resubscribed successfully.'}, status=status.HTTP_200_OK)

from twilio.twiml.voice_response import VoiceResponse, Dial

class MakeCallView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from_number = request.data.get('from_number')
        to_number = request.data.get('to_number')

        if not from_number or not to_number:
            return Response({'error': 'Both "from_number" and "to_number" are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user owns the "from" number
        if not TwilioNumber.objects.filter(user=request.user, phone_number=from_number, subscription_status='active').exists():
            return Response({'error': 'You do not own this number or it is inactive.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Check user's balance
            wallet = Wallet.objects.get(user=request.user)
            service_rate = ServiceRate.objects.filter(service_type='outbound_call').first()

            if not service_rate:
                return Response({'error': 'Calling service rate not configured.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # We can't know the call duration yet, but we can check if the user has a positive balance
            if wallet.balance <= 0:
                return Response({'error': 'Insufficient balance to make a call.'}, status=status.HTTP_400_BAD_REQUEST)

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            # The URL for Twilio to send webhook requests to
            callback_url = request.build_absolute_uri(f'/api/twilio/voice-callback/?to_number={to_number}')

            call = client.calls.create(
                to=to_number,
                from_=from_number,
                url=callback_url,
                method='GET',
                status_callback=request.build_absolute_uri('/api/twilio/call-status/'),
                status_callback_method='POST',
                status_callback_event=['completed']
            )

            twilio_number = TwilioNumber.objects.get(phone_number=from_number)
            Call.objects.create(
                user=request.user,
                twilio_number=twilio_number,
                call_sid=call.sid,
                from_number=from_number,
                to_number=to_number,
                direction='outbound'
            )

            return Response({'sid': call.sid, 'status': 'Call initiated successfully.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Twilio API error while making a call: {e}")
            return Response({'error': 'Failed to initiate call.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VoiceCallbackView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        to_number = request.query_params.get('to_number')
        if not to_number:
            return Response({'error': '"to_number" query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        response = VoiceResponse()
        dial = Dial()
        dial.number(to_number)
        response.append(dial)

        return Response(str(response), content_type='text/xml')

class CallStatusView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        call_sid = request.data.get('CallSid')
        call_status = request.data.get('CallStatus')
        call_duration = request.data.get('CallDuration')
        from_number = request.data.get('From')

        if call_status == 'completed':
            try:
                twilio_number = TwilioNumber.objects.get(phone_number=from_number)
                user = twilio_number.user
                wallet = Wallet.objects.get(user=user)
                service_rate = ServiceRate.objects.filter(service_type='outbound_call').first()

                if service_rate and call_duration:
                    duration_minutes = (int(call_duration) + 59) // 60  # Round up to the nearest minute
                    cost = duration_minutes * service_rate.rate
                    wallet.balance -= cost
                    wallet.save()
                    logger.info(f"Charged {cost} from user {user.email} for call {call_sid}")

                    try:
                        call = Call.objects.get(call_sid=call_sid)
                        call.duration = int(call_duration)
                        call.cost = cost
                        call.save()
                    except Call.DoesNotExist:
                        logger.error(f"Call with SID {call_sid} not found in the database.")

            except TwilioNumber.DoesNotExist:
                logger.error(f"Call status callback for non-existent Twilio number: {from_number}")
            except Wallet.DoesNotExist:
                logger.error(f"Wallet not found for user of number: {from_number}")
            except ServiceRate.DoesNotExist:
                logger.error(f"Service rate for outbound calls not configured.")
            except Exception as e:
                logger.error(f"Error processing call status callback: {e}")

        return Response(status=status.HTTP_204_NO_CONTENT)

class SendSMSView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from_number = request.data.get('from_number')
        to_number = request.data.get('to_number')
        body = request.data.get('body')

        if not all([from_number, to_number, body]):
            return Response({'error': '"from_number", "to_number", and "body" are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not TwilioNumber.objects.filter(user=request.user, phone_number=from_number, subscription_status='active').exists():
            return Response({'error': 'You do not own this number or its subscription is inactive.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            wallet = Wallet.objects.get(user=request.user)
            service_rate = ServiceRate.objects.filter(service_type='outbound_sms').first()

            if not service_rate:
                return Response({'error': 'SMS service rate not configured.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if wallet.balance < service_rate.rate:
                return Response({'error': 'Insufficient balance to send SMS.'}, status=status.HTTP_400_BAD_REQUEST)

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                to=to_number,
                from_=from_number,
                body=body
            )
            
            wallet.balance -= service_rate.rate
            wallet.save()

            twilio_number = TwilioNumber.objects.get(phone_number=from_number)
            Message.objects.create(
                user=request.user,
                twilio_number=twilio_number,
                message_sid=message.sid,
                from_number=from_number,
                to_number=to_number,
                body=body,
                direction='outbound'
            )
            
            return Response({'sid': message.sid, 'status': 'SMS sent successfully.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Twilio API error while sending SMS: {e}")
            return Response({'error': 'Failed to send SMS.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class IncomingSMSView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        from_number = request.data.get('From')
        to_number = request.data.get('To')
        body = request.data.get('Body')
        message_sid = request.data.get('MessageSid')

        logger.info(f'Incoming SMS from {from_number} to {to_number}: {body}')

        try:
            twilio_number = TwilioNumber.objects.get(phone_number=to_number)
            Message.objects.create(
                user=twilio_number.user,
                twilio_number=twilio_number,
                message_sid=message_sid,
                from_number=from_number,
                to_number=to_number,
                body=body,
                direction='inbound',
                status='received'
            )
        except TwilioNumber.DoesNotExist:
            logger.error(f"Incoming SMS to non-existent Twilio number: {to_number}")

        return Response(status=status.HTTP_204_NO_CONTENT)




class IncomingCallView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        from_number = request.data.get('From')
        to_number = request.data.get('To')
        call_sid = request.data.get('CallSid')

        try:
            twilio_number = TwilioNumber.objects.get(phone_number=to_number)
            user = twilio_number.user

            Call.objects.create(
                user=user,
                twilio_number=twilio_number,
                call_sid=call_sid,
                from_number=from_number,
                to_number=to_number,
                direction='inbound'
            )

            wallet = Wallet.objects.get(user=user)
            service_rate = ServiceRate.objects.filter(service_type='inbound_call').first()

            if not service_rate:
                logger.warning("Inbound call service rate not configured.")
                response = VoiceResponse()
                response.hangup()
                return Response(str(response), content_type='text/xml')

            if wallet.balance < service_rate.rate: # Check for at least one minute cost
                logger.warning(f"User {user.email} has insufficient balance for incoming call.")
                response = VoiceResponse()
                response.hangup()
                return Response(str(response), content_type='text/xml')
            
            if user.phone_number:
                response = VoiceResponse()
                dial = Dial(
                    caller_id=from_number
                )
                dial.number(user.phone_number)
                response.append(dial)
                return Response(str(response), content_type='text/xml')
            else:
                response = VoiceResponse()
                response.hangup()
                return Response(str(response), content_type='text/xml')
        except TwilioNumber.DoesNotExist:
            response = VoiceResponse()
            response.hangup()
            return Response(str(response), content_type='text/xml')


        total_calls = Call.objects.filter(user=user).count()
        unread_messages = Message.objects.filter(user=user, is_read=False).count()

        data = {
            'active_numbers': active_numbers,
            'total_calls': total_calls,
            'unread_messages': unread_messages
        }

        return Response(data)


class InboundCallStatusView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        call_sid = request.data.get('CallSid')
        call_status = request.data.get('DialCallStatus')
        call_duration = request.data.get('DialCallDuration')
        twilio_number_str = request.data.get('To')

        if call_status == 'completed':
            try:
                twilio_number = TwilioNumber.objects.get(phone_number=twilio_number_str)
                user = twilio_number.user
                wallet = Wallet.objects.get(user=user)
                service_rate = ServiceRate.objects.filter(service_type='inbound_call').first()

                if service_rate and call_duration:
                    duration_minutes = (int(call_duration) + 59) // 60  # Round up to the nearest minute
                    cost = duration_minutes * service_rate.rate
                    wallet.balance -= cost
                    wallet.save()
                    logger.info(f"Charged {cost} from user {user.email} for inbound call {call_sid}")

                    try:
                        call = Call.objects.get(call_sid=call_sid)
                        call.duration = int(call_duration)
                        call.cost = cost
                        call.save()
                    except Call.DoesNotExist:
                        logger.error(f"Call with SID {call_sid} not found in the database.")

            except TwilioNumber.DoesNotExist:
                logger.error(f"Inbound call status callback for non-existent Twilio number: {twilio_number_str}")
            except Wallet.DoesNotExist:
                logger.error(f"Wallet not found for user of number: {twilio_number_str}")
            except ServiceRate.DoesNotExist:
                logger.error(f"Service rate for inbound calls not configured.")
            except Exception as e:
                logger.error(f"Error processing inbound call status callback: {e}")

        return Response(status=status.HTTP_204_NO_CONTENT)


class CallHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CallSerializer

    def get_queryset(self):
        return Call.objects.filter(user=self.request.user).order_by('-timestamp')


class ConversationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        user = self.request.user
        messages = Message.objects.filter(user=user).order_by('-timestamp')
        
        conversations = {}
        for message in messages:
            # Determine the other party's number
            if message.direction == 'inbound':
                other_party_number = message.from_number
            else: # outbound
                other_party_number = message.to_number
            
            if other_party_number not in conversations:
                conversations[other_party_number] = {
                    'with_number': other_party_number,
                    'last_message': message, # First message in sorted list is the latest
                    'messages': []
                }
            conversations[other_party_number]['messages'].append(message)
        
        return list(conversations.values())
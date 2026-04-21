from rest_framework import serializers
from .models import TwilioNumber, Country, Call, Message

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['name', 'code']

class TwilioNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwilioNumber
        fields = ['id', 'sid', 'phone_number', 'friendly_name', 'price', 'subscription_status', 'subscription_end_date', 'purchased_at']

class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'body', 'timestamp', 'direction', 'is_read')


class ConversationSerializer(serializers.Serializer):
    with_number = serializers.CharField()
    last_message = MessageSerializer()
    messages = MessageSerializer(many=True)
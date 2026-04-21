from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime

class TwilioNumberPrice(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)

    def __str__(self):
        return f"NGN {self.price}"

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name_plural = "Countries"

class TwilioNumber(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='twilio_numbers')
    sid = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    friendly_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    subscription_status = models.CharField(max_length=20, default='active')
    subscription_end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.friendly_name} ({self.phone_number})'

    @property
    def is_active(self):
        return self.subscription_status == 'active' and self.subscription_end_date > timezone.now()

class ServiceRate(models.Model):
    SERVICE_CHOICES = [
        ('outbound_call', 'Outbound Call (per minute)'),
        ('inbound_call', 'Inbound Call (per minute)'),
        ('outbound_sms', 'Outbound SMS (per message)'),
        ('inbound_sms', 'Inbound SMS (per message)'),
    ]
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES, unique=True)
    rate = models.DecimalField(max_digits=10, decimal_places=4, help_text="Cost per unit of service")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_service_type_display()} - {self.rate}"

class Call(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calls')
    twilio_number = models.ForeignKey(TwilioNumber, on_delete=models.CASCADE, related_name='calls')
    call_sid = models.CharField(max_length=255, unique=True)
    from_number = models.CharField(max_length=20)
    to_number = models.CharField(max_length=20)
    duration = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    direction = models.CharField(max_length=10, choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')])

    def __str__(self):
        return f'Call {self.call_sid} from {self.from_number} to {self.to_number}'

class Message(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages')
    twilio_number = models.ForeignKey(TwilioNumber, on_delete=models.CASCADE, related_name='messages')
    message_sid = models.CharField(max_length=255, unique=True)
    from_number = models.CharField(max_length=20)
    to_number = models.CharField(max_length=20)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    direction = models.CharField(max_length=10, choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')])

    def __str__(self):
        return f'Message {self.message_sid} from {self.from_number} to {self.to_number}'
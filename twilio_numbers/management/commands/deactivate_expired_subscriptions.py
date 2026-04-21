from django.core.management.base import BaseCommand
from twilio_numbers.models import TwilioNumber
from django.utils import timezone

class Command(BaseCommand):
    help = 'Deactivates expired Twilio number subscriptions'

    def handle(self, *args, **options):
        expired_numbers = TwilioNumber.objects.filter(
            subscription_end_date__lt=timezone.now(),
            subscription_status='active'
        )
        for number in expired_numbers:
            number.subscription_status = 'inactive'
            number.save()
            self.stdout.write(self.style.SUCCESS(f'Deactivated subscription for {number.phone_number}'))
from django.core.management.base import BaseCommand
from twilio_numbers.models import Country

class Command(BaseCommand):
    help = "Populates the Country table with a list of countries and their codes"

    def handle(self, *args, **kwargs):
        countries = [
            {"name": "United States", "code": "US"},
            {"name": "Canada", "code": "CA"},
            {"name": "United Kingdom", "code": "GB"},
            # Add more countries as needed
        ]

        for country_data in countries:
            Country.objects.get_or_create(name=country_data["name"], defaults={"code": country_data["code"]})

        self.stdout.write(self.style.SUCCESS("Successfully populated countries"))

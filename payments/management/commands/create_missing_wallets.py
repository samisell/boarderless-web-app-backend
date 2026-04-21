from django.core.management.base import BaseCommand
from users.models import User
from payments.models import Wallet

class Command(BaseCommand):
    help = 'Create missing wallets for existing users'

    def handle(self, *args, **options):
        users_without_wallets = User.objects.filter(wallet__isnull=True)
        for user in users_without_wallets:
            Wallet.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS(f'Successfully created wallet for {user.email}'))
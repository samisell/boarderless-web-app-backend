from django.db import models
from django.conf import settings

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unit_balance = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user.username}\'s Wallet'


class UnitUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='unit_usage')
    units_used = models.PositiveIntegerField()
    service_description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} used {self.units_used} units for {self.service_description}'

class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=[
        ('fund', 'Fund'),
        ('purchase', 'Purchase'),
        ('call', 'Call'),
        ('unit_purchase', 'Unit Purchase'),
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.transaction_type} of {self.amount} for {self.wallet.user.username}'


class Unit(models.Model):
    name = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.name} - {self.price}'


class UnitPurchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='unit_purchases')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} purchased {self.quantity} of {self.unit.name}'
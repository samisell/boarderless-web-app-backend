from rest_framework import serializers
from .models import Wallet, Transaction, Unit, UnitPurchase


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'name', 'price']


class UnitPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitPurchase
        fields = ['id', 'user', 'unit', 'quantity', 'total_price', 'timestamp']
        read_only_fields = ['user', 'total_price', 'timestamp']


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance']
        read_only_fields = ['user', 'balance']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'wallet', 'transaction_type', 'amount', 'reference', 'timestamp']
        read_only_fields = ['wallet', 'timestamp']
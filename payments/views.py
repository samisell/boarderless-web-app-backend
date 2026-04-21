import requests
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Wallet, Transaction, Unit, UnitPurchase
from .serializers import WalletSerializer, TransactionSerializer, UnitSerializer, UnitPurchaseSerializer


class UnitListView(generics.ListAPIView):
    """
    Retrieves the list of available units.
    """
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [permissions.IsAuthenticated]


class UnitPurchaseView(APIView):
    """
    Handles the purchase of units.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        unit_id = request.data.get('unit_id')
        quantity = request.data.get('quantity')

        if not unit_id or not quantity:
            return Response({'error': 'Unit ID and quantity are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            unit = Unit.objects.get(id=unit_id)
            quantity = int(quantity)
        except (Unit.DoesNotExist, ValueError):
            return Response({'error': 'Invalid unit ID or quantity'}, status=status.HTTP_400_BAD_REQUEST)

        total_price = unit.price * quantity
        wallet = Wallet.objects.get(user=request.user)

        if wallet.balance < total_price:
            return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

        wallet.balance -= total_price
        wallet.unit_balance += quantity
        wallet.save()

        unit_purchase = UnitPurchase.objects.create(
            user=request.user,
            unit=unit,
            quantity=quantity,
            total_price=total_price,
        )

        Transaction.objects.create(
            wallet=wallet,
            transaction_type='unit_purchase',
            amount=total_price,
            reference=f'unit-purchase-{unit_purchase.id}',
        )

        return Response(UnitPurchaseSerializer(unit_purchase).data, status=status.HTTP_201_CREATED)


class UseUnitView(APIView):
    """
    Handles the spending of units for a service.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        units_to_use = request.data.get('units_to_use')
        service_description = request.data.get('service_description')

        if not units_to_use or not service_description:
            return Response({'error': 'Units to use and service description are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            units_to_use = int(units_to_use)
        except ValueError:
            return Response({'error': 'Invalid units to use'}, status=status.HTTP_400_BAD_REQUEST)

        wallet = Wallet.objects.get(user=request.user)

        if wallet.unit_balance < units_to_use:
            return Response({'error': 'Insufficient unit balance'}, status=status.HTTP_400_BAD_REQUEST)

        wallet.unit_balance -= units_to_use
        wallet.save()

        UnitUsage.objects.create(
            user=request.user,
            units_used=units_to_use,
            service_description=service_description,
        )

        return Response({'message': 'Units used successfully'}, status=status.HTTP_200_OK)


class WalletView(generics.RetrieveAPIView):
    """
    Retrieves the wallet for the authenticated user.
    """
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Wallet.objects.get(user=self.request.user)


class TransactionListView(generics.ListAPIView):
    """
    Retrieves the list of transactions for the authenticated user.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        wallet = Wallet.objects.get(user=self.request.user)
        return Transaction.objects.filter(wallet=wallet)


class InitializePaymentView(APIView):
    """
    Initializes a payment transaction with Paystack.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        amount = request.data.get('amount')
        email = request.user.email

        if not amount:
            return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)

        url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        data = {
            'email': email,
            'amount': int(amount),  # Paystack expects amount in kobo
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raise an exception for bad status codes
            return Response(response.json(), status=status.HTTP_200_OK)
        except requests.exceptions.RequestException as e:
            try:
                error_response = e.response.json()
                return Response(error_response, status=e.response.status_code)
            except (AttributeError, ValueError):
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyPaymentView(APIView):
    """
    Verifies a payment transaction with Paystack and updates the user's wallet.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        reference = request.query_params.get('reference')

        if not reference:
            return Response({'error': 'Reference is required'}, status=status.HTTP_400_BAD_REQUEST)

        url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()['data']

            if data['status'] == 'success':
                if Transaction.objects.filter(reference=reference).exists():
                    return Response({'message': 'Transaction already verified'}, status=status.HTTP_200_OK)

                wallet = Wallet.objects.get(user=request.user)
                amount = data['amount'] / 100  # Convert back to Naira

                Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='fund',
                    amount=amount,
                    reference=reference,
                )

                wallet.balance += amount
                wallet.save()

                return Response({'message': 'Payment successful', 'balance': wallet.balance}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Payment failed'}, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            try:
                error_response = e.response.json()
                return Response(error_response, status=e.response.status_code)
            except (AttributeError, ValueError):
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InitializeFlutterwavePaymentView(APIView):
    """
    Initializes a payment transaction with Flutterwave.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        tx_ref = request.data.get('tx_ref')
        email = request.user.email
        amount = request.data.get('amount')

        if tx_ref:
            # If tx_ref is provided, re-initialize the payment
            # You might want to add validation here to ensure the user owns this tx_ref
            pass
        else:
            # If no tx_ref, create a new transaction
            if not amount:
                return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)
            tx_ref = f'hustle-{request.user.id}-{Transaction.objects.count()}'

        url = 'https://api.flutterwave.com/v3/payments'
        headers = {
            'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        data = {
            'tx_ref': tx_ref,
            'amount': amount,
            'currency': 'NGN',
            'redirect_url': request.data.get('redirect_url', 'http://localhost:3000/wallet'),
            'customer': {
                'email': email,
                'name': request.user.username,
            },
            'customizations': {
                'title': 'Borderless Network Wallet Funding',
                'description': 'Fund your wallet to purchase services.',
            },
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json()
            response_data['tx_ref'] = data['tx_ref']
            return Response(response_data, status=status.HTTP_200_OK)
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyFlutterwavePaymentView(APIView):
    """
    Verifies a payment transaction with Flutterwave and updates the user's wallet.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        transaction_id = request.query_params.get('transaction_id')

        if not transaction_id:
            return Response({'error': 'Transaction ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not transaction_id.isdigit():
            return Response({'error': 'Invalid Transaction ID format. Expected an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        url = f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify'
        headers = {
            'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}',
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()['data']

            if data['status'] == 'successful':
                # Check if transaction has already been processed to prevent double crediting
                if Transaction.objects.filter(reference=data['tx_ref']).exists():
                    return Response({'message': 'Transaction already verified'}, status=status.HTTP_200_OK)

                wallet = Wallet.objects.get(user=request.user)
                amount = data['amount']

                Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='fund',
                    amount=amount,
                    reference=data['tx_ref'],
                )

                wallet.balance += amount
                wallet.save()

                return Response({'message': 'Payment successful', 'balance': wallet.balance}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Payment failed'}, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            try:
                error_response = e.response.json()
                return Response(error_response, status=e.response.status_code)
            except (AttributeError, ValueError):
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
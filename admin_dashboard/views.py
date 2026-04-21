from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from twilio_numbers.models import Country, TwilioNumber
from twilio_numbers.forms import CountryForm
from payments.models import Transaction, UnitPurchase, UnitUsage
from users.models import User
from referrals.models import Referral
from site_settings.models import SystemSetting


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure the user is a logged-in staff member."""
    def test_func(self):
        return self.request.user.is_staff


class SystemSettingsView(StaffRequiredMixin, UpdateView):
    model = SystemSetting
    fields = ['number_purchase_amount', 'call_unit_rate', 'message_unit_rate']
    template_name = 'admin_dashboard/system_settings.html'
    success_url = reverse_lazy('admin_dashboard:system-settings')

    def get_object(self, queryset=None):
        # Get the first SystemSetting object, or create one if it doesn't exist
        obj, created = SystemSetting.objects.get_or_create(pk=1)
        return obj


class AdminLoginView(View):
    def get(self, request):
        form = AuthenticationForm()
        return render(request, 'admin_dashboard/login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                return redirect('admin_dashboard:dashboard')
        return render(request, 'admin_dashboard/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('admin_dashboard:login')


@login_required
def dashboard(request):
    total_users = User.objects.count()
    total_payments = Transaction.objects.count()
    total_twilio_numbers = TwilioNumber.objects.count()
    total_referrals = Referral.objects.count()

    context = {
        'total_users': total_users,
        'total_payments': total_payments,
        'total_twilio_numbers': total_twilio_numbers,
        'total_referrals': total_referrals,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


class UserListView(StaffRequiredMixin, ListView):
    queryset = User.objects.order_by('email')
    template_name = 'admin_dashboard/user_list.html'
    context_object_name = 'users'
    paginate_by = 15 # Add pagination for better performance

class TransactionListView(StaffRequiredMixin, ListView):
    model = Transaction
    template_name = 'admin_dashboard/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        return Transaction.objects.select_related('wallet__user').order_by('-timestamp')


class UnitPurchaseListView(StaffRequiredMixin, ListView):
    model = UnitPurchase
    template_name = 'admin_dashboard/unit_purchase_list.html'
    context_object_name = 'unit_purchases'
    paginate_by = 10
    queryset = UnitPurchase.objects.order_by('-timestamp').select_related('user', 'unit')


class UnitUsageListView(StaffRequiredMixin, ListView):
    model = UnitUsage
    template_name = 'admin_dashboard/unit_usage_list.html'
    context_object_name = 'unit_usages'
    paginate_by = 10
    queryset = UnitUsage.objects.order_by('-timestamp').select_related('user')


class ReferralListView(StaffRequiredMixin, ListView):
    model = Referral
    template_name = 'admin_dashboard/referral_list.html'
    context_object_name = 'referrals'
    paginate_by = 10
    queryset = Referral.objects.select_related('referrer', 'referred').order_by('-timestamp')


class CountryListView(StaffRequiredMixin, ListView):
    model = Country
    template_name = 'admin_dashboard/country_list.html'
    context_object_name = 'countries'

class CountryCreateView(StaffRequiredMixin, CreateView):
    model = Country
    form_class = CountryForm
    template_name = 'admin_dashboard/country_form.html'
    success_url = reverse_lazy('admin_dashboard:country_list')

class CountryUpdateView(StaffRequiredMixin, UpdateView):
    model = Country
    form_class = CountryForm
    template_name = 'admin_dashboard/country_form.html'
    success_url = reverse_lazy('admin_dashboard:country_list')


class TwilioNumberListView(StaffRequiredMixin, ListView):
    model = TwilioNumber
    template_name = 'admin_dashboard/twilio_number_list.html'
    context_object_name = 'twilio_numbers'
    paginate_by = 15

    def get_queryset(self):
        return TwilioNumber.objects.select_related('user').order_by('-purchased_at')

class CountryDeleteView(StaffRequiredMixin, DeleteView):
    model = Country
    template_name = 'admin_dashboard/country_confirm_delete.html'
    success_url = reverse_lazy('admin_dashboard:country_list')
from django.contrib import admin
from .models import Country, TwilioNumber, TwilioNumberPrice, ServiceRate

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(TwilioNumber)
class TwilioNumberAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'friendly_name', 'user', 'price', 'purchased_at')
    search_fields = ('phone_number', 'friendly_name', 'user__username')
    list_filter = ('purchased_at',)

@admin.register(TwilioNumberPrice)
class TwilioNumberPriceAdmin(admin.ModelAdmin):
    list_display = ('price',)

@admin.register(ServiceRate)
class ServiceRateAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'rate', 'description')
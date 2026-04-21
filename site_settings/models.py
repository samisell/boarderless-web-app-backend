from django.db import models

class SystemSetting(models.Model):
    number_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    call_unit_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.10)
    message_unit_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.50)

    def __str__(self):
        return "System Settings"
from django.db import models
from django.conf import settings

class Referral(models.Model):
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='referrals_made', on_delete=models.CASCADE)
    referred = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='referred_by', on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referrer} referred {self.referred or 'N/A'}"
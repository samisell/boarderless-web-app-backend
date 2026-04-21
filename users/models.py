from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    email = models.EmailField(unique=True, verbose_name='email address')
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    full_address = models.TextField(blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bundle_sid = models.CharField(max_length=34, blank=True, null=True)  # A Twilio Bundle SID is 34 characters long, starting with BU

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def is_otp_valid(self):
        if not self.otp_created_at:
            return False
        return (timezone.now() - self.otp_created_at).total_seconds() < 300  # 5 minutes

    def __str__(self):
        return self.email
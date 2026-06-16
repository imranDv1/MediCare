from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    DEFAULT_AVATAR = 'https://placehold.co/100x100?text=User'

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('pharmacist', 'Pharmacist'),
        ('staff', 'Staff'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.URLField(max_length=500, blank=True, default='')

    @property
    def avatar_url(self):
        return self.avatar or self.DEFAULT_AVATAR

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

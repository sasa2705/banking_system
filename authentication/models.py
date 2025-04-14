from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Custom user model to add additional fields and relationships"""
    is_admin = models.BooleanField(default=False)
    account_no = models.IntegerField(null=True, blank=True)
    
    def __str__(self) -> str:
        return self.username

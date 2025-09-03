from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    profile_picture = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # plan control
    plan = models.CharField(max_length=20, choices=(
        ("free", "Free"),
        ("pro", "Pro"),
    ), default="free")

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    class Meta:
        db_table = 'auth_user'


class Shortcode(models.Model):
    """Each shortcode belongs to an admin (our registered user)."""
    admin = models.OneToOneField(User, on_delete=models.CASCADE, related_name="shortcode")
    code = models.CharField(max_length=20, unique=True, default=uuid.uuid4().hex[:8])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.username} - {self.code}"




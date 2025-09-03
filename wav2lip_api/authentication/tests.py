from django.test import TestCase
import unittest

from .models import User

# Create your tests here.

def create_users():
    user1 = User.objects.create_user(
        username="aryan01",
        email="aryan01@example.com",
        first_name="Aryan",
        last_name="Agrawal",
        phone_number="9876543210",
        password="password123",
        profile_picture="https://example.com/images/aryan.jpg",
        is_online=True
    )

    user2 = User.objects.create_user(
        username="riya02",
        email="riya02@example.com",
        first_name="Riya",
        last_name="Sharma",
        phone_number="9123456780",
        password="password456",
        profile_picture="https://example.com/images/riya.jpg",
        is_online=False
    )

    print("✅ Users created successfully!")
    print(user1)
    print(user2)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import transaction
from .models import User
from .serializers import ReactUserSerializer
import logging

logger = logging.getLogger(__name__)

class ReactSignupView(APIView):
    """
    React UI Signup endpoint
    Fields: username, age, email, phone, password
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            # Extract data from React UI
            username = request.data.get('username')
            age = request.data.get('age')
            email = request.data.get('email')
            phone = request.data.get('phone')
            password = request.data.get('password')

            # Basic validation
            if not all([username, age, email, phone, password]):
                return Response({
                    'error': 'All fields are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return Response({
                    'error': 'Email already exists. Please use a different email.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate age
            try:
                age = int(age)
                if age < 13 or age > 120:
                    return Response({
                        'error': 'Age must be between 13 and 120'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({
                    'error': 'Invalid age value'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create user with transaction
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    full_name=username,  # Map username to full_name
                    age=age,
                    phone=phone,
                    role='alumni'  # Default role
                )

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                return Response({
                    'message': 'Account created successfully!',
                    'user': {
                        'id': user.id,
                        'username': user.full_name,  # Return as username for React
                        'age': user.age,
                        'email': user.email,
                        'phone': user.phone,
                        'createdAt': user.created_at.isoformat()
                    },
                    'tokens': {
                        'access': access_token,
                        'refresh': str(refresh)
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Signup error: {str(e)}", exc_info=True)
            return Response({
                'error': 'An error occurred during signup. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReactLoginView(APIView):
    """
    React UI Login endpoint
    Fields: email, password
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')

            if not email or not password:
                return Response({
                    'error': 'Email and password are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Authenticate user
            user = authenticate(request, email=email, password=password)
            
            if not user:
                return Response({
                    'error': 'Invalid email or password'
                }, status=status.HTTP_401_UNAUTHORIZED)

            if not user.is_active:
                return Response({
                    'error': 'Account is deactivated'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # Update last login
            user.save()

            return Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.full_name or 'User',  # Return as username for React
                    'age': user.age,
                    'email': user.email,
                    'phone': user.phone,
                    'createdAt': user.created_at.isoformat()
                },
                'tokens': {
                    'access': access_token,
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return Response({
                'error': 'An error occurred during login. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReactUserProfileView(APIView):
    """
    React UI User Profile endpoint
    Requires authentication
    """
    def get(self, request):
        """Get user profile"""
        try:
            user = request.user
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.full_name or 'User',
                    'age': user.age,
                    'email': user.email,
                    'phone': user.phone,
                    'createdAt': user.created_at.isoformat()
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Profile get error: {str(e)}", exc_info=True)
            return Response({
                'error': 'An error occurred while fetching profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        """Update user profile"""
        try:
            user = request.user
            data = request.data.copy()

            # Update allowed fields
            if 'username' in data:
                user.full_name = data['username']
            if 'age' in data:
                user.age = data['age']
            if 'phone' in data:
                user.phone = data['phone']

            user.save()

            return Response({
                'message': 'Profile updated successfully',
                'user': {
                    'id': user.id,
                    'username': user.full_name or 'User',
                    'age': user.age,
                    'email': user.email,
                    'phone': user.phone,
                    'createdAt': user.created_at.isoformat()
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Profile update error: {str(e)}", exc_info=True)
            return Response({
                'error': 'An error occurred while updating profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

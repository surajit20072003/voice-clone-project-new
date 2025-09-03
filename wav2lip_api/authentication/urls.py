from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LogoutView, RegisterView, LoginView, \
    ProfileView, UsersListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('users/', UsersListView.as_view(), name='users_list'),
    path('logout/', LogoutView.as_view(), name='jwt_logout'),
]
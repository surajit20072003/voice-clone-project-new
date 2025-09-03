from django.urls import path
from .views import AdminUploadVideo

urlpatterns = [
    path('upload/', AdminUploadVideo.as_view(), name='admin-upload-video'),
]

from django.urls import path
from django.shortcuts import render
from .views import (
    GenerateLipSyncView,
    GenerateFromBrowserTextToVideoView,
    GenerateOnlyTextAnswerView,
    TaskStatusView,
)

# --- NEW IMPORTS ---
from django.conf import settings
from django.conf.urls.static import static
# --- NEW IMPORTS ---

urlpatterns = [
    # HTML Routes (These can remain the same)
    path('', lambda request: render(request, 'generate_lipsync.html'), name='generate-lipsync-ui'),
    path('generate-from-text-page/', lambda request: render(request, 'generate_from_text.html'), name='generate-from-text-ui'),
    path('only-text-answer-page/', lambda request: render(request, 'only_text_answer.html'), name='generate-text-only-ui'),

    # API Endpoints
    path('api/generate/', GenerateLipSyncView.as_view(), name='generate-lipsync'),
    path('api/generate/from-text/', GenerateFromBrowserTextToVideoView.as_view(), name='generate-from-text'),
    path('api/generate/text-only/', GenerateOnlyTextAnswerView.as_view(), name='generate-text-only'),
    
    # Add this new URL for checking task status
    path('api/task-status/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
]

# --- NEW LINE: Add a URL pattern to serve media files ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# --- NEW LINE ---


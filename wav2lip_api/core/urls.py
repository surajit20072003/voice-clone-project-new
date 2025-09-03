from django.urls import path
from django.shortcuts import render
from .views import (
    GenerateLipSync,
    GenerateFromBrowserTextToVideo,
    GenerateOnlyTextAnswer,
    
)

urlpatterns = [
    # HTML Routes
    path('', lambda request: render(request, 'generate_lipsync.html'), name='generate-lipsync-ui'),
    path('generate-from-text-page/', lambda request: render(request, 'generate_from_text.html'), name='generate-from-text-ui'),
    path('only-text-answer-page/', lambda request: render(request, 'only_text_answer.html'), name='generate-text-only-ui'),

    # API Endpoints
    path('api/generate/', GenerateLipSync.as_view(), name='generate-lipsync'),
    path('api/generate/from-text/', GenerateFromBrowserTextToVideo.as_view(), name='generate-from-text'),
    path('api/generate/text-only/', GenerateOnlyTextAnswer.as_view(), name='generate-text-only'),
    
]
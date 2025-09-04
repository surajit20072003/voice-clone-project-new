import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from celery.result import AsyncResult
from django.http import FileResponse, Http404
from django.conf import settings
from .models import UserVideo
from .tasks import process_lip_sync_task, text_to_video_task, generate_llama_response_task

class GenerateLipSyncView(APIView):
    """
    API endpoint to initiate a new lip-sync video generation task.
    Accepts video file, text, speaker_id, and language.
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        video_file = request.FILES.get('video')
        input_text = request.data.get('text')
        speaker_id = request.data.get('speaker_id')
        lang = request.data.get('lang')
        
        if not all([video_file, input_text, speaker_id, lang]):
            return Response({'error': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the user's video and create a UserVideo instance
        user_video = UserVideo.objects.create(
            user=request.user if request.user.is_authenticated else None,
            speaker_id=speaker_id,
            video_file=video_file,
            status='PENDING' 
        )

        # Offload the heavy processing to a Celery worker
        task = process_lip_sync_task.delay(
            user_video_pk=user_video.pk, 
            input_text=input_text, 
            lang=lang
        )

        # Return a 202 status to indicate the task has been accepted
        return Response(
            {'message': 'Your video processing task has started.', 'task_id': task.id}, 
            status=status.HTTP_202_ACCEPTED
        )


class GenerateFromBrowserTextToVideoView(APIView):
    """
    API endpoint to generate a video from a text prompt using an existing speaker profile.
    """
    def post(self, request):
        input_text = request.data.get('text')
        speaker_id = request.data.get('speaker_id')
        lang = request.data.get('lang')

        if not all([input_text, speaker_id, lang]):
            return Response({'error': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)

        # Offload the text-to-video generation to a Celery worker
        task = text_to_video_task.delay(
            input_text=input_text,
            speaker_id=speaker_id,
            lang=lang
        )

        # Return a 202 status to indicate the task has been accepted
        return Response(
            {'message': 'Your text-to-video task has started.', 'task_id': task.id},
            status=status.HTTP_202_ACCEPTED
        )


class GenerateOnlyTextAnswerView(APIView):
    """
    API endpoint to generate a text-only answer using Llama3.
    """
    def post(self, request):
        user_input = request.data.get('text')
        if not user_input:
            return Response({'error': 'Text input is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        summarization_prompt = f"simple in 1-2 line English sentences, only answer,always check and clarify the answer: \n{user_input}"
        
        # Offload the Llama3 text generation to a Celery worker
        task = generate_llama_response_task.delay(prompt=summarization_prompt)

        # Return a 202 status to indicate the task has been accepted
        return Response(
            {'message': 'Your text generation task has started.', 'task_id': task.id},
            status=status.HTTP_202_ACCEPTED
        )


class TaskStatusView(APIView):
    """
    API endpoint to check the status of a specific background task using its task_id.
    """
    def get(self, request, task_id):
        task_result = AsyncResult(task_id)
        result = {
            "task_id": task_id,
            "task_status": task_result.status,
            "task_result": task_result.result if task_result.status != 'FAILURE' else str(task_result.result)
        }
        if task_result.status == 'PROGRESS':
            result['progress'] = task_result.info.get('status', 'In progress...')
        return Response(result, status=status.HTTP_200_OK)

class TaskResultView(APIView):
    """
    API endpoint to retrieve the final result (e.g., the generated video file)
    of a completed task.
    """
    def get(self, request, task_id):
        task_result = AsyncResult(task_id)

        # Check if the task is done
        if not task_result.ready():
            return Response({'message': 'Task is not yet complete. Current status: ' + task_result.status}, status=status.HTTP_200_OK)

        # Check if the task failed
        if task_result.failed():
            return Response({'error': 'Task failed. Reason: ' + str(task_result.result)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Get the result from the task
        result_data = task_result.get()
        result_path = result_data.get('result_url')

        if not result_path:
            return Response({'error': 'Task completed, but no result path was found.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Use absolute path to serve the file
        full_path = os.path.join(settings.BASE_DIR, result_path)
        if not os.path.exists(full_path):
            raise Http404(f"File not found at {full_path}")
        
        # Serve the file to the client
        return FileResponse(open(full_path, 'rb'), content_type='video/mp4')
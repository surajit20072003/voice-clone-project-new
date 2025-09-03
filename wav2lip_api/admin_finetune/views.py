from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from core.models import UserVideo
import uuid

class AdminUploadVideo(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        try:
            video_file = request.FILES.get('video')
            
            if not video_file:
                return Response({'error': 'Video is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            generated_speaker_id = str(uuid.uuid4())

            user_video = UserVideo.objects.create(
                user=request.user,
                speaker_id=generated_speaker_id,
                video_file=video_file,
                is_admin_uploaded=True,
                is_approved_for_finetuning=True
            )

            return Response({
                'message': 'Admin video uploaded successfully. It is ready for the fine-tuning pipeline.',
                'speaker_id': generated_speaker_id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
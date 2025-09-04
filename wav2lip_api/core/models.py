from django.db import models
from authentication.models import User
# Create your models here.
class UserVideo(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    speaker_id = models.CharField(max_length=255, unique=True)
    video_file = models.FileField(upload_to='user_uploads/')
    status = models.CharField(max_length=20, default='PENDING')
    is_processed = models.BooleanField(default=False)
    is_approved_for_finetuning = models.BooleanField(default=False)
    is_admin_uploaded = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Video by {self.user.username if self.user else 'Anonymous'}"

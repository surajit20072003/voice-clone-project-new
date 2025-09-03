from django.contrib import admin
from core.models import UserVideo
from django.utils.translation import gettext_lazy as _

# Import your two separate Celery tasks
from admin_finetune.tasks import run_syncnet_finetuning_task, run_wav2lip_finetuning_task

@admin.register(UserVideo)
class UserVideoAdmin(admin.ModelAdmin):
    list_display = ('speaker_id', 'video_file', 'is_approved_for_finetuning', 'uploaded_at')
    list_filter = ('is_approved_for_finetuning', 'speaker_id')
    search_fields = ('speaker_id',)
    
    # Define two separate actions for the two-step process
    actions = ['start_syncnet_finetuning', 'start_wav2lip_finetuning']

    def start_syncnet_finetuning(self, request, queryset):
        """
        Admin action to start the SyncNet fine-tuning task.
        """
        video_ids = list(queryset.values_list('id', flat=True))
        
        if not video_ids:
            self.message_user(request, "No videos were selected.", level='error')
            return

        # Trigger the SyncNet fine-tuning task. It will also handle preprocessing.
        run_syncnet_finetuning_task.delay(video_ids)
        
        self.message_user(
            request,
            _("SyncNet fine-tuning process initiated for %(count)d videos. Monitor the Celery worker and terminate it manually when satisfied with the training progress.") % {'count': len(video_ids)}
        )
    start_syncnet_finetuning.short_description = "Start SyncNet fine-tuning"

    def start_wav2lip_finetuning(self, request, queryset):
        """
        Admin action to start the Wav2Lip fine-tuning task.
        """
        video_ids = list(queryset.values_list('id', flat=True))

        if not video_ids:
            self.message_user(request, "No videos were selected.", level='error')
            return

        # Trigger the Wav2Lip fine-tuning task.
        # This task assumes SyncNet fine-tuning has already been performed.
        run_wav2lip_finetuning_task.delay(video_ids)
        
        self.message_user(
            request,
            _("Wav2Lip fine-tuning process initiated for %(count)d videos. This will use the latest SyncNet model from the previous step.") % {'count': len(video_ids)}
        )
    start_wav2lip_finetuning.short_description = "Start Wav2Lip fine-tuning"
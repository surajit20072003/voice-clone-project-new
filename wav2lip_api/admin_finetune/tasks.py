import os
import subprocess
import json
from celery import shared_task
from django.conf import settings
from core.models import UserVideo
import shutil
import uuid

# Define paths for the pre-trained models.
PRETRAINED_SYNCNET_PATH = os.path.join(settings.MEDIA_ROOT, 'checkpoints', 'syncnet_pretrained.pth')
PRETRAINED_WAV2LIP_PATH = os.path.join(settings.MEDIA_ROOT, 'checkpoints', 'wav2lip_pretrained.pth')

def _prepare_data(video_ids):
    """
    Helper function to perform data staging and preprocessing.
    Returns the path to the preprocessed data root.
    """
    approved_videos = UserVideo.objects.filter(id__in=video_ids, is_approved_for_finetuning=True)
    
    if not approved_videos:
        print("No videos approved for fine-tuning. Exiting.")
        return None

    temp_data_root = os.path.join(settings.MEDIA_ROOT, 'temp_finetune_data', str(uuid.uuid4()))
    preprocessed_root = os.path.join(settings.MEDIA_ROOT, 'finetune_data')
    syncnet_checkpoint_dir = os.path.join(settings.MEDIA_ROOT, 'checkpoints', 'syncnet')
    wav2lip_checkpoint_dir = os.path.join(settings.MEDIA_ROOT, 'checkpoints', 'wav2lip')
    wav2lip_repo_path = "/home/surajit/voice_clone_project/Wav2Lip"

    os.makedirs(temp_data_root, exist_ok=True)
    os.makedirs(preprocessed_root, exist_ok=True)
    os.makedirs(syncnet_checkpoint_dir, exist_ok=True)
    os.makedirs(wav2lip_checkpoint_dir, exist_ok=True)

    try:
        for video in approved_videos:
            speaker_dir = os.path.join(temp_data_root, video.speaker_id)
            os.makedirs(speaker_dir, exist_ok=True)
            shutil.copy(video.video_file.path, os.path.join(speaker_dir, os.path.basename(video.video_file.path)))

        print("Data staging complete. Starting preprocessing...")
        
        subprocess.run([
            "python", "preprocess.py",
            "--data_root", temp_data_root,
            "--preprocessed_root", preprocessed_root,
        ], cwd=wav2lip_repo_path, check=True)
        
        print("Preprocessing successful.")
        
        # Clean up the temporary raw video staging directory
        if os.path.exists(temp_data_root):
            shutil.rmtree(temp_data_root)

    except Exception as e:
        if os.path.exists(temp_data_root):
            shutil.rmtree(temp_data_root)
        print(f"Data preparation or preprocessing failed: {e}")
        raise e
    
    return preprocessed_root

@shared_task
def run_syncnet_finetuning_task(video_ids):
    """
    Celery task to run SyncNet fine-tuning.
    """
    preprocessed_root = _prepare_data(video_ids)
    if not preprocessed_root:
        return
        
    print("Preprocessing complete. Starting SyncNet fine-tuning...")
    
    wav2lip_repo_path = "/home/surajit/voice_clone_project/Wav2Lip"
    syncnet_checkpoint_dir = os.path.join(settings.MEDIA_ROOT, 'checkpoints', 'syncnet')
    
    try:
        command = [
            "python", "color_syncnet_train.py",
            "--data_root", preprocessed_root,
            "--checkpoint_dir", syncnet_checkpoint_dir,
        ]
        if os.path.exists(PRETRAINED_SYNCNET_PATH):
            command.extend(["--checkpoint_path", PRETRAINED_SYNCNET_PATH])
        
        subprocess.run(command, cwd=wav2lip_repo_path)
        print("SyncNet fine-tuning process started. Monitor the worker manually.")
    except Exception as e:
        print(f"Failed to start SyncNet fine-tuning process: {e}")
        raise e

@shared_task
def run_wav2lip_finetuning_task(video_ids):
    """
    Celery task to run Wav2Lip fine-tuning.
    """
    preprocessed_root = os.path.join(settings.MEDIA_ROOT, 'finetune_data')
    if not os.path.exists(preprocessed_root):
        print("Preprocessed data not found. Run SyncNet task first to generate data. Exiting.")
        return

    wav2lip_repo_path = "/home/surajit/voice_clone_project/Wav2Lip"
    syncnet_checkpoint_dir = os.path.join(settings.MEDIA_ROOT, 'checkpoints', 'syncnet')
    wav2lip_checkpoint_dir = os.path.join(settings.MEDIA_ROOT, 'checkpoints', 'wav2lip')
    
    try:
        syncnet_checkpoints = sorted(
            [os.path.join(syncnet_checkpoint_dir, f) for f in os.listdir(syncnet_checkpoint_dir) if f.endswith('.pth')],
            key=os.path.getmtime
        )
        if not syncnet_checkpoints:
            print("No SyncNet checkpoint found. Run SyncNet task first to train the model. Exiting.")
            return

        latest_syncnet_checkpoint = syncnet_checkpoints[-1]
        
        print("Latest SyncNet checkpoint found. Starting Wav2Lip fine-tuning...")

        command = [
            "python", "wav2lip_train.py",
            "--data_root", preprocessed_root,
            "--checkpoint_dir", wav2lip_checkpoint_dir,
            "--syncnet_checkpoint_path", latest_syncnet_checkpoint,
        ]
        if os.path.exists(PRETRAINED_WAV2LIP_PATH):
            command.extend(["--checkpoint_path", PRETRAINED_WAV2LIP_PATH])

        subprocess.run(command, cwd=wav2lip_repo_path, check=True)
        print("Wav2Lip fine-tuning pipeline completed successfully!")

    except Exception as e:
        print(f"Wav2Lip fine-tuning failed: {e}")
        raise e
    finally:
        # NEW: Clean up the preprocessed data folder after the final step
        preprocessed_root = os.path.join(settings.MEDIA_ROOT, 'finetune_data')
        if os.path.exists(preprocessed_root):
            shutil.rmtree(preprocessed_root)
            print("Preprocessed data cleaned up.")
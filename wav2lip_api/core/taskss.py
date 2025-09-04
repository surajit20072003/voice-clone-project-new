
import os
import subprocess
import json
import uuid
import logging
import re
import math
import random
import shutil
import time
from celery import shared_task, current_task
from django.conf import settings
from gtts import gTTS
from .models import UserVideo

logger = logging.getLogger(__name__)

# --- Celery-Safe Helper Functions ---

def get_tts_model_celery():
    """Loads TTS model with GPU support."""
    try:
        from TTS.api import TTS
        return TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False, gpu=True)
    except Exception as e:
        logger.error(f"Failed to load TTS model: {e}", exc_info=True)
        raise Exception("TTS model not available. Check your installation and configuration.")

def get_ollama_client_celery():
    """Loads and tests Ollama client."""
    try:
        import ollama as ol
        ol.chat(model='llama3', messages=[{'role': 'user', 'content': 'Test LLaMA3'}])
        return ol
    except Exception as e:
        logger.error(f"Failed to connect to LLaMA3: {e}", exc_info=True)
        raise Exception("Ollama client not available. Is the server running and 'llama3' pulled?")

def get_inflect_engine_celery():
    """Loads inflect engine."""
    try:
        import inflect
        return inflect.engine()
    except Exception as e:
        logger.warning(f"Inflect library not found: {e}. Number-to-words conversion will be skipped.")
        return None

def convert_numbers_to_words(text):
    """Converts numbers in text to their word form."""
    p_engine = get_inflect_engine_celery()
    if p_engine is None:
        return text
    try:
        return re.sub(r'\d+', lambda match: p_engine.number_to_words(match.group()), text)
    except Exception as e:
        logger.warning(f"Inflect conversion failed: {e}. Using original text.")
        return text

def run_wav2lip_full(input_video_path, audio_path, output_path, checkpoint_path, inference_dir):
    """Executes the Wav2Lip inference script using GPU."""
    logger.info(f"Running Wav2Lip on GPU: face='{input_video_path}', audio='{audio_path}', output='{output_path}'")
    abs_checkpoint_path = os.path.abspath(checkpoint_path)
    abs_input_video_path = os.path.abspath(input_video_path)
    abs_audio_path = os.path.abspath(audio_path)
    abs_output_path = os.path.abspath(output_path)
    abs_inference_dir = os.path.abspath(inference_dir)

    if not os.path.exists(abs_checkpoint_path):
        raise FileNotFoundError(f"Wav2Lip checkpoint not found: {abs_checkpoint_path}")
    if not os.path.exists(abs_input_video_path):
        raise FileNotFoundError(f"Input face video not found: {abs_input_video_path}")
    if not os.path.exists(abs_audio_path):
        raise FileNotFoundError(f"Audio file not found: {abs_audio_path}")
    if not os.path.isdir(abs_inference_dir):
        raise FileNotFoundError(f"Wav2Lip inference directory not found: {abs_inference_dir}")

    try:
        command = [
            "python3", "inference.py",
            "--checkpoint_path", abs_checkpoint_path,
            "--face", abs_input_video_path,
            "--audio", abs_audio_path,
            "--outfile", abs_output_path,
            "--resize_factor", "2",
            "--pads", "0", "10", "0", "0"
        ]
        
        result = subprocess.run(
            command,
            cwd=abs_inference_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        logger.info(f"Wav2Lip stdout: {result.stdout}")
        logger.info(f"Wav2Lip stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        error_message = f"Wav2Lip subprocess failed. Stderr: {e.stderr}"
        logger.error(error_message, exc_info=True)
        raise Exception(error_message)


def _process_video_and_audio_for_lipsync(video_path, audio_ref_path, input_text, lang, temp_dir):
    """
    Processes a source video and text into a final video/audio pair for Wav2Lip,
    using looping if needed via concatenation.
    """
    start_time = time.time()
    logger.info("Starting _process_video_and_audio_for_lipsync...")
    
    uid = str(uuid.uuid4())
    tts_audio_path = os.path.join(temp_dir, f"{uid}_tts.mp3")
    slowed_audio_path = os.path.join(temp_dir, f"{uid}_tts_slow.wav")
    final_video_input_path = os.path.join(temp_dir, f"{uid}_video_input.mp4")

    # Generate TTS audio
    tts_start = time.time()
    if lang == 'en':
        tts_engine = get_tts_model_celery()
        tts_engine.tts_to_file(text=input_text, speaker_wav=audio_ref_path, file_path=tts_audio_path, language="en")
    elif lang == 'hi':
        tts = gTTS(text=input_text, lang='hi')
        tts.save(tts_audio_path)
    else:
        raise ValueError(f"Unsupported language: {lang}")
    logger.info(f"TTS audio generation time: {time.time() - tts_start:.2f} seconds")

    # Determine audio duration and slow it down
    slow_audio_start = time.time()
    audio_duration_output = subprocess.check_output(["ffprobe", "-i", tts_audio_path, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"], text=True).strip()
    original_audio_duration = float(audio_duration_output)
    
    target_duration_factor = 1.2
    slow_factor = 1 / target_duration_factor
    subprocess.run(["ffmpeg", "-y", "-i", tts_audio_path, "-filter:a", f"atempo={slow_factor}", slowed_audio_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    slowed_audio_duration = original_audio_duration * target_duration_factor
    logger.info(f"Audio slowing time: {time.time() - slow_audio_start:.2f} seconds")

    # --- Naya logic: video ko loop karne ke liye ---
    video_prep_start = time.time()
    
    video_duration_output = subprocess.check_output([
        "ffprobe", "-i", video_path, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"
    ], text=True).strip()
    source_video_duration = float(video_duration_output)

    # Calculate how many times to loop the video
    num_loops = math.ceil(slowed_audio_duration / source_video_duration)
    
    # Create a temporary list file for concatenation
    temp_concat_list_path = os.path.join(temp_dir, f"{uid}_loop_list.txt")
    with open(temp_concat_list_path, 'w') as f:
        for _ in range(num_loops):
            f.write(f"file '{video_path}'\n")

    # Concatenate the video multiple times
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", temp_concat_list_path, 
        "-t", str(slowed_audio_duration), "-c", "copy", "-an", "-loglevel", "quiet",
        final_video_input_path
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    logger.info(f"Video preparation time: {time.time() - video_prep_start:.2f} seconds")
    logger.info(f"Total video & audio preparation time: {time.time() - start_time:.2f} seconds")
    
    return final_video_input_path, slowed_audio_path, tts_audio_path

# --- Celery Tasks ---

@shared_task(bind=True)
def generate_llama_response_task(self, prompt):
    """Celery task for generating text with Llama3."""
    start_time = time.time()
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Generating text...'})
        ollama_client = get_ollama_client_celery()
        response = ollama_client.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
        llama_answer = response['message']['content']
        logger.info(f"Llama3 response generation time: {time.time() - start_time:.2f} seconds")
        return {'status': 'COMPLETE', 'answer': llama_answer}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e

@shared_task(bind=True)
def process_lip_sync_task(self, user_video_pk, input_text, lang):
    """Celery task for the main video generation process."""
    user_video = None
    start_time = time.time()
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Initializing task...'})
        user_video = UserVideo.objects.get(pk=user_video_pk)
        
        media_root = settings.MEDIA_ROOT
        input_video_path = user_video.video_file.path
        speaker_id = user_video.speaker_id
        
        speaker_dir = os.path.join(media_root, 'speakers', speaker_id)
        temp_dir = os.path.join(media_root, 'temp')
        os.makedirs(speaker_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        
        self.update_state(state='PROGRESS', meta={'status': 'Preparing speaker profile...'})
        prep_start_time = time.time()
        stored_audio_path = os.path.join(speaker_dir, "voice_reference.wav")
        subprocess.run(["ffmpeg", "-y", "-i", input_video_path, "-q:a", "0", "-map", "a", stored_audio_path], check=True, capture_output=True)
        logger.info(f"Speaker profile preparation time: {time.time() - prep_start_time:.2f} seconds")

        self.update_state(state='PROGRESS', meta={'status': 'Generating voice and staging video...'})
        
        final_video_input_path, slowed_audio_path, tts_audio_path = _process_video_and_audio_for_lipsync(
            video_path=input_video_path,
            audio_ref_path=stored_audio_path,
            input_text=input_text,
            lang=lang,
            temp_dir=temp_dir
        )
        
        self.update_state(state='PROGRESS', meta={'status': 'Running Wav2Lip inference...'})
        
        inference_start = time.time()
        uid = str(uuid.uuid4())
        final_output_path = os.path.join(temp_dir, f"{uid}_result.mp4")
        
        checkpoint_path = os.path.join(settings.BASE_DIR, "Wav2Lip/checkpoints/wav2lip_gan.pth")
        inference_dir = os.path.join(settings.BASE_DIR, "Wav2Lip")

        run_wav2lip_full(
            input_video_path=final_video_input_path,
            audio_path=slowed_audio_path,
            output_path=final_output_path,
            checkpoint_path=checkpoint_path,
            inference_dir=inference_dir
        )
        logger.info(f"Wav2Lip inference time: {time.time() - inference_start:.2f} seconds")

        if not os.path.exists(final_output_path):
            raise Exception(f"Wav2Lip did not produce the expected output file: {final_output_path}")

        user_video.generated_video_path = final_output_path
        user_video.status = 'COMPLETE'
        user_video.save()
        
        relative_path = os.path.relpath(final_output_path, settings.MEDIA_ROOT)
        result_url = os.path.join(settings.MEDIA_URL, relative_path)
        
        logger.info(f"Total task execution time: {time.time() - start_time:.2f} seconds")
        
        return {'status': 'COMPLETE', 'result_url': result_url}

    except Exception as e:
        logger.error(f"Task failed for user_video_pk {user_video_pk}: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        if user_video:
            user_video.status = 'FAILED'
            user_video.save()
        raise e

@shared_task(bind=True)
def text_to_video_task(self, input_text, speaker_id, lang):
    """Celery task for text-to-video generation with an existing speaker."""
    final_output_path = None
    start_time = time.time()
    
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Looking for speaker profile...'})
        speaker_dir = os.path.join(settings.MEDIA_ROOT, 'speakers', speaker_id)
        stored_audio_path = os.path.join(speaker_dir, "voice_reference.wav")
        
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        if not os.path.exists(stored_audio_path):
            raise FileNotFoundError(f"Speaker profile not found for ID: {speaker_id}")
        
        get_video_start = time.time()
        try:
            user_video = UserVideo.objects.get(speaker_id=speaker_id)
            original_video_path = user_video.video_file.path
        except UserVideo.DoesNotExist:
            raise FileNotFoundError(f"Original video not found for speaker ID: {speaker_id}")
        logger.info(f"Video lookup time: {time.time() - get_video_start:.2f} seconds")

        self.update_state(state='PROGRESS', meta={'status': 'Generating conversational text with Llama3...'})
        
        llama_start = time.time()
        conversational_prompt = (
            f"As a helpful and friendly AI assistant, respond naturally and conversationally "
            f"to the following query. Keep your answer concise, ideally within 1-2 sentences, "
            f"and make it sound like a real person talking: \n{input_text}"
        )
        ollama_client = get_ollama_client_celery()
        response = ollama_client.chat(model='llama3', messages=[{'role': 'user', 'content': conversational_prompt}])
        generated_answer = response['message']['content']
        cleaned_text = convert_numbers_to_words(generated_answer)
        logger.info(f"Llama3 generation time: {time.time() - llama_start:.2f} seconds")

        self.update_state(state='PROGRESS', meta={'status': 'Preparing video and audio for lip-sync...'})
        
        final_video_input_path, slowed_audio_path, tts_audio_path = _process_video_and_audio_for_lipsync(
            video_path=original_video_path,
            audio_ref_path=stored_audio_path,
            input_text=cleaned_text,
            lang=lang,
            temp_dir=temp_dir
        )

        self.update_state(state='PROGRESS', meta={'status': 'Running Wav2Lip inference on GPU...'})
        
        inference_start = time.time()
        uid = str(uuid.uuid4())
        final_output_path = os.path.join(temp_dir, f"{uid}_result.mp4")
        
        checkpoint_path = os.path.join(settings.BASE_DIR, "Wav2Lip/checkpoints/wav2lip_gan.pth")
        inference_dir = os.path.join(settings.BASE_DIR, "Wav2Lip")

        run_wav2lip_full(
            input_video_path=final_video_input_path,
            audio_path=slowed_audio_path,
            output_path=final_output_path,
            checkpoint_path=checkpoint_path,
            inference_dir=inference_dir
        )
        logger.info(f"Wav2Lip inference time: {time.time() - inference_start:.2f} seconds")

        if not os.path.exists(final_output_path):
            raise Exception(f"Wav2Lip did not produce the expected output file: {final_output_path}")
        
        relative_path = os.path.relpath(final_output_path, settings.MEDIA_ROOT)
        result_url = os.path.join(settings.MEDIA_URL, relative_path)
        
        logger.info(f"Total task execution time: {time.time() - start_time:.2f} seconds")
        
        return {'status': 'COMPLETE', 'result_url': result_url}
    
    except Exception as e:
        logger.error(f"Text-to-video task failed for speaker {speaker_id}: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e

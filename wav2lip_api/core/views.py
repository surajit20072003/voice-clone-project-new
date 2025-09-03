import os
import uuid
import subprocess
import re
import json
import random
import math
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.http import FileResponse
from django.shortcuts import render
from gtts import gTTS
from .models import UserVideo
from rest_framework.permissions import AllowAny

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

# --- Global Initializations (Deferred Loading) ---
# We will use helper functions to load these models on demand
tts_model = None
p = None
ollama = None

def get_tts_model():
    """Loads TTS model if not already loaded."""
    global tts_model
    if tts_model is None:
        try:
            from TTS.api import TTS
            tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False, gpu=False)
            logger.info("TTS model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}", exc_info=True)
            raise Exception("TTS model not available. Check your installation and configuration.")
    return tts_model

def get_inflect_engine():
    """Loads inflect engine if not already loaded."""
    global p
    if p is None:
        try:
            import inflect
            p = inflect.engine()
            logger.info("Inflect engine loaded successfully.")
        except Exception as e:
            logger.warning(f"Inflect library not found or failed to load: {e}. Number-to-words conversion will be skipped.", exc_info=True)
    return p

def get_ollama_client():
    """Loads and tests Ollama client if not already loaded."""
    global ollama
    if ollama is None:
        try:
            import ollama as ol
            response = ol.chat(model='llama3', messages=[{'role': 'user', 'content': 'Test LLaMA3'}])
            ollama = ol
            logger.info("LLaMA3 and Ollama connection successful.")
        except Exception as e:
            logger.error(f"Failed to connect to LLaMA3: {e}", exc_info=True)
            raise Exception("Ollama client not available. Is the server running and 'llama3' pulled?")
    return ollama

# --- Utility Functions (Refactored) ---
def run_wav2lip_full(input_video_path, audio_path, output_path, checkpoint_path, inference_dir):
    """
    Executes the Wav2Lip inference script.
    """
    logger.info(f"Running Wav2Lip: face='{input_video_path}', audio='{audio_path}', output='{output_path}'")
    
    # Ensure all paths are absolute before passing to subprocess
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
        result = subprocess.run([
            "python3", "inference.py",
            "--checkpoint_path", abs_checkpoint_path,
            "--face", abs_input_video_path,
            "--audio", abs_audio_path,
            "--outfile", abs_output_path,
            "--resize_factor", "2",
            "--pads", "0", "10", "0", "0"
        ], cwd=abs_inference_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

        logger.info(f"Wav2Lip stdout: {result.stdout}")
        logger.info(f"Wav2Lip stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        error_message = (
            f"Wav2Lip subprocess failed with exit code {e.returncode}.\n"
            f"Command: {' '.join(e.cmd)}\n"
            f"Stdout: {e.stdout}\n"
            f"Stderr: {e.stderr}"
        )
        logger.error(error_message, exc_info=True)
        raise Exception(error_message)
    except Exception as e:
        logger.error(f"Error running Wav2Lip subprocess: {e}", exc_info=True)
        raise

def generate_llama_response(prompt):
    """
    Generates a conversational response using the LLaMA3 model.
    """
    ollama_client = get_ollama_client()
    try:
        response = ollama_client.chat(model='llama3', messages=[
            {'role': 'user', 'content': prompt}
        ])
        llama_answer = response['message']['content']
        return llama_answer
    except Exception as e:
        logger.error(f"LLaMA 3 generation failed: {e}", exc_info=True)
        raise Exception(f"LLaMA 3 generation failed. Is Ollama running and is 'llama3' model pulled? Error: {str(e)}")

def convert_numbers_to_words(text):
    """
    Converts numbers in text to their word form.
    """
    p_engine = get_inflect_engine()
    if p_engine is None:
        return text
    try:
        return re.sub(r'\d+', lambda match: p_engine.number_to_words(match.group()), text)
    except Exception as e:
        logger.warning(f"Inflect conversion failed: {e}. Using original text.", exc_info=True)
        return text

# --- Helper Method for Common Processing ---
def _process_video_and_audio_for_lipsync(
    video_path, 
    audio_ref_path, 
    input_text, 
    lang, 
    temp_dir, 
    clip_paths
):
    """
    Processes video clips and text into a final video/audio pair for Wav2Lip.
    """
    uid = str(uuid.uuid4())
    tts_audio_path = os.path.join(temp_dir, f"{uid}_tts.mp3")
    slowed_audio_path = os.path.join(temp_dir, f"{uid}_tts_slow.wav")
    temp_concat_list_path = os.path.join(temp_dir, f"{uid}_clip_list.txt")
    temp_concat_clip_path = os.path.join(temp_dir, f"{uid}_concat.mp4")
    final_video_input_path = os.path.join(temp_dir, f"{uid}_video_input.mp4")

    # Generate TTS audio
    if lang == 'en':
        tts_engine = get_tts_model()
        tts_engine.tts_to_file(text=input_text, speaker_wav=audio_ref_path, file_path=tts_audio_path, language="en")
    elif lang == 'hi':
        tts = gTTS(text=input_text, lang='hi')
        tts.save(tts_audio_path)
    else:
        raise ValueError(f"Unsupported language: {lang}")

    # Determine audio duration
    audio_duration_output = subprocess.check_output([
        "ffprobe", "-i", tts_audio_path, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"
    ], text=True).strip()
    original_audio_duration = float(audio_duration_output)
    
    # Calculate required slowdown factor for a more natural pace
    target_duration_factor = 1.2 # Make the output 20% slower than the original TTS audio
    slow_factor = 1 / target_duration_factor
    
    # Slow down the audio
    subprocess.run(["ffmpeg", "-y", "-i", tts_audio_path, "-filter:a", f"atempo={slow_factor}", slowed_audio_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    slowed_audio_duration = original_audio_duration * target_duration_factor
    
    # Prepare video for concatenation
    clip_duration_secs = 5
    num_clips_needed = math.ceil(slowed_audio_duration / clip_duration_secs)
    selected_clips = (clip_paths * num_clips_needed)[:num_clips_needed]

    with open(temp_concat_list_path, 'w') as f:
        for clip in selected_clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", temp_concat_list_path, "-c", "copy", "-an",
        temp_concat_clip_path
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Merge slowed video with slowed audio
    subprocess.run([
        "ffmpeg", "-y", "-i", temp_concat_clip_path,
        "-i", slowed_audio_path,
        "-c:v", "libx264", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        "-t", str(slowed_audio_duration), # Truncate video to match slowed audio duration
        final_video_input_path
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return final_video_input_path, slowed_audio_path

# --- API View Classes ---
class GenerateLipSync(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            video_file = request.FILES.get('video')
            input_text = request.data.get('text')
            speaker_id = request.data.get('speaker_id')
            lang = request.data.get('lang')
            
            # Authenticated user ko get karein
            current_user = request.user if request.user.is_authenticated else None

            if not video_file or not input_text or not speaker_id or not lang:
                return Response({'error': 'Video, text, speaker_id, and language are required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if a video with the given speaker_id already exists for this user
            if current_user and UserVideo.objects.filter(user=current_user, speaker_id=speaker_id).exists():
                 return Response({'error': f'A video with speaker_id "{speaker_id}" already exists for this user.'}, status=status.HTTP_409_CONFLICT)
            elif not current_user and UserVideo.objects.filter(speaker_id=speaker_id).exists():
                 return Response({'error': f'A video with speaker_id "{speaker_id}" already exists.'}, status=status.HTTP_409_CONFLICT)


            # --- Naya Logic: Video ko Database mein save karna ---
            user_video = UserVideo.objects.create(
                user=current_user,
                speaker_id=speaker_id,
                video_file=video_file,
                # Fine-tuning ke liye approval ka status False set karein
                is_approved_for_finetuning=False 
            )
            # Database mein save karne ke baad, video file ka path mil jayega
            input_video_path = user_video.video_file.path

            # Speaker directory banane ke liye user dwara diya gaya speaker_id ka upyog karein
            speaker_dir = f'media/speakers/{speaker_id}'
            os.makedirs(speaker_dir, exist_ok=True)
            
            # Video se audio extract karein
            input_audio_path = os.path.join(speaker_dir, "voice_reference.wav")
            subprocess.run(["ffmpeg", "-y", "-i", input_video_path, "-q:a", "0", "-map", "a", input_audio_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stored_audio_path = input_audio_path

            # Video clips banayein
            video_duration_output = subprocess.check_output([
                "ffprobe", "-i", input_video_path, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"
            ], text=True).strip()
            video_duration = float(video_duration_output)
            clip_paths = []
            clip_duration_secs = 5
            for i in range(int(video_duration // clip_duration_secs)):
                start_time = i * clip_duration_secs
                clip_path = os.path.join(speaker_dir, f"clip_{i}.mp4")
                subprocess.run([
                    "ffmpeg", "-y", "-ss", str(start_time), "-i", input_video_path,
                    "-t", str(clip_duration_secs), "-c", "copy", "-an", clip_path
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if os.path.exists(clip_path):
                    clip_paths.append(clip_path)

            if not clip_paths:
                return Response({'error': 'Video was too short to create clips.'}, status=status.HTTP_400_BAD_REQUEST)

            clips_file_path = os.path.join(speaker_dir, "clips.json")
            with open(clips_file_path, 'w') as f:
                json.dump(clip_paths, f)
            
            # TTS audio aur final video output banayein
            uid = str(uuid.uuid4())
            base_dir_temp = 'media/temp'
            os.makedirs(base_dir_temp, exist_ok=True)
            final_output_video_path = os.path.join(base_dir_temp, f"{uid}_result.mp4")

            final_video_input_path, slowed_audio_path = _process_video_and_audio_for_lipsync(
                video_path=input_video_path,
                audio_ref_path=stored_audio_path,
                input_text=input_text,
                lang=lang,
                temp_dir=base_dir_temp,
                clip_paths=clip_paths
            )

            run_wav2lip_full(
                input_video_path=final_video_input_path,
                audio_path=slowed_audio_path,
                output_path=final_output_video_path,
                checkpoint_path="../Wav2Lip/checkpoints/wav2lip_gan.pth",
                inference_dir="../Wav2Lip"
            )

            if not os.path.exists(final_output_video_path):
                raise Exception(f"Wav2Lip did not produce the expected output file: {final_output_video_path}")

            return FileResponse(open(final_output_video_path, 'rb'), content_type='video/mp4')

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            return Response({'error': f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Sirf temporary files delete karein. Original uploaded video aur speaker data database mein rahega.
            # ... (cleanup logic remains the same)
            pass

class GenerateFromBrowserTextToVideo(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        final_output_video_path = None
        final_video_input_path = None
        slowed_audio_path = None
        uid = None
        
        try:
            input_text = request.data.get('text')
            speaker_id = request.data.get('speaker_id')
            lang = request.data.get('lang')

            if not input_text or not speaker_id or not lang:
                return Response({'error': 'Text, speaker_id, and language are required.'}, status=status.HTTP_400_BAD_REQUEST)

            speaker_dir = f'media/speakers/{speaker_id}'
            stored_audio_path = os.path.join(speaker_dir, "voice_reference.wav")
            clips_file_path = os.path.join(speaker_dir, "clips.json")

            if not os.path.exists(stored_audio_path) or not os.path.exists(clips_file_path):
                return Response({'error': f'Speaker profile not found for ID: {speaker_id}. Please register a speaker using the /generate_lipsync/ endpoint first.'}, status=status.HTTP_404_NOT_FOUND)

            with open(clips_file_path, 'r') as f:
                clip_paths = json.load(f)
            
            if not clip_paths:
                return Response({'error': f'No video clips found for speaker ID: {speaker_id}.'}, status=status.HTTP_404_NOT_FOUND)

            conversational_prompt = (
                f"As a helpful and friendly AI assistant, respond naturally and conversationally "
                f"to the following query. Keep your answer concise, ideally within 1-2 sentences, "
                f"and make it sound like a real person talking: \n{input_text}"
            )
            generated_answer = generate_llama_response(conversational_prompt)
            cleaned_text = convert_numbers_to_words(generated_answer)
            
            base_dir = 'media/temp'
            os.makedirs(base_dir, exist_ok=True)
            uid = str(uuid.uuid4())
            final_output_video_path = os.path.join(base_dir, f"{uid}_result.mp4")

            final_video_input_path, slowed_audio_path = _process_video_and_audio_for_lipsync(
                video_path=None, # Not used in this function, but kept for consistency
                audio_ref_path=stored_audio_path,
                input_text=cleaned_text,
                lang=lang,
                temp_dir=base_dir,
                clip_paths=clip_paths
            )

            run_wav2lip_full(
                input_video_path=final_video_input_path,
                audio_path=slowed_audio_path,
                output_path=final_output_video_path,
                checkpoint_path="../Wav2Lip/checkpoints/wav2lip_gan.pth",
                inference_dir="../Wav2Lip"
            )

            if not os.path.exists(final_output_video_path):
                raise Exception(f"Wav2Lip did not produce the expected output file: {final_output_video_path}")

            return FileResponse(open(final_output_video_path, 'rb'), content_type='video/mp4')

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            return Response({'error': f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if 'uid' in locals():
                paths_to_clean = [
                    final_output_video_path, final_video_input_path, slowed_audio_path,
                    os.path.join('media/temp', f"{uid}_clip_list.txt"),
                    os.path.join('media/temp', f"{uid}_concat.mp4"),
                    os.path.join('media/temp', f"{uid}_tts.mp3"),
                    os.path.join('media/temp', f"{uid}_tts_slow.wav")
                ]
                for path in paths_to_clean:
                    if path and os.path.exists(path):
                        try:
                            os.remove(path)
                        except Exception as e:
                            logger.error(f"Error cleaning up temporary file '{path}': {e}", exc_info=True)


class GenerateOnlyTextAnswer(APIView):
    parser_classes = (FormParser,)
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get('text')

        if not user_input:
            logger.warning("Missing text input for GenerateOnlyTextAnswer.")
            return Response({'error': 'Text input is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            summarization_prompt = f"simple in 1-2 line English sentences, only answer,always check and clarify the answer: \n{user_input}"
            generated_answer = generate_llama_response(summarization_prompt)
            return Response({'answer': generated_answer}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"An unexpected error occurred in GenerateOnlyTextAnswer: {e}", exc_info=True)
            return Response({'error': f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
import sys
import argparse
import os
from os import path, makedirs
import cv2
import traceback
import subprocess
from tqdm import tqdm
from glob import glob
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

if sys.version_info[0] < 3 and sys.version_info[1] < 2:
    raise Exception("Must be using >= Python 3.2")

if not path.isfile('face_detection/detection/sfd/s3fd.pth'):
    raise FileNotFoundError('Save the s3fd model to face_detection/detection/sfd/s3fd.pth \
                            before running this script!')

import face_detection

parser = argparse.ArgumentParser()
parser.add_argument('--ngpu', help='Number of GPUs across which to run in parallel', default=1, type=int)
parser.add_argument('--batch_size', help='Single GPU Face detection batch size', default=16, type=int)
parser.add_argument("--data_root", help="Root folder of the LRS2 dataset", required=True)
parser.add_argument("--preprocessed_root", help="Root folder of the preprocessed dataset", required=True)
args = parser.parse_args()

fa = [face_detection.FaceAlignment(face_detection.LandmarksType._2D, flip_input=False, 
                                    device='cuda:{}'.format(id)) for id in range(args.ngpu)]

template = 'ffmpeg -loglevel panic -y -i {} -strict -2 {}'

def process_video_file(vfile, args, gpu_id):
    video_stream = cv2.VideoCapture(vfile)
    frames = []
    while True:
        still_reading, frame = video_stream.read()
        if not still_reading:
            video_stream.release()
            break
        frames.append(frame)
    
    vidname = path.basename(vfile).split('.')[0]
    dirname = vfile.split('/')[-2]
    fulldir = path.join(args.preprocessed_root, dirname, vidname)
    makedirs(fulldir, exist_ok=True)

    batches = [frames[i:i + args.batch_size] for i in range(0, len(frames), args.batch_size)]
    i = -1
    for fb in batches:
        preds = fa[gpu_id].get_detections_for_batch(np.asarray(fb))
        for j, f in enumerate(preds):
            i += 1
            if f is None:
                continue
            x1, y1, x2, y2 = f
            cv2.imwrite(path.join(fulldir, '{}.jpg'.format(i)), fb[j][y1:y2, x1:x2])

def process_audio_file(vfile, args):
    vidname = path.basename(vfile).split('.')[0]
    dirname = vfile.split('/')[-2]
    fulldir = path.join(args.preprocessed_root, dirname, vidname)
    makedirs(fulldir, exist_ok=True)
    wavpath = path.join(fulldir, 'audio.wav')
    command = template.format(vfile, wavpath)
    subprocess.call(command, shell=True)

def mp_handler(job):
    vfile, args, gpu_id = job
    try:
        process_video_file(vfile, args, gpu_id)
    except KeyboardInterrupt:
        exit(0)
    except:
        traceback.print_exc()

def generate_file_lists(preprocessed_root):
    """Generates train.txt and val.txt from the preprocessed data."""
    all_speakers = glob(path.join(preprocessed_root, '*'))
    all_videos = []
    for speaker_dir in all_speakers:
        all_videos.extend(glob(path.join(speaker_dir, '*')))

    # Randomly shuffle the list of all video paths
    random.shuffle(all_videos)

    # Split the dataset into train and validation (95% / 5%)
    split_point = int(len(all_videos) * 0.95)
    train_videos = all_videos[:split_point]
    val_videos = all_videos[split_point:]

    # Write the paths to the file lists
    filelist_dir = path.join(preprocessed_root, 'filelists')
    makedirs(filelist_dir, exist_ok=True)

    with open(path.join(filelist_dir, 'train.txt'), 'w') as f:
        for v in train_videos:
            rel_path = path.relpath(v, preprocessed_root)
            f.write(f'{rel_path}\n')

    with open(path.join(filelist_dir, 'val.txt'), 'w') as f:
        for v in val_videos:
            rel_path = path.relpath(v, preprocessed_root)
            f.write(f'{rel_path}\n')
            
    print("File lists (train.txt and val.txt) created successfully.")

def main(args):
    print('Started processing for {} with {} GPUs'.format(args.data_root, args.ngpu))
    filelist = glob(path.join(args.data_root, '*/*.mp4'))
    
    if not filelist:
        print("No video files found. Exiting.")
        return

    jobs = [(vfile, args, i % args.ngpu) for i, vfile in enumerate(filelist)]
    p = ThreadPoolExecutor(args.ngpu)
    futures = [p.submit(mp_handler, j) for j in jobs]
    _ = [r.result() for r in tqdm(as_completed(futures), total=len(futures))]
    
    print('Dumping audios...')
    for vfile in tqdm(filelist):
        try:
            process_audio_file(vfile, args)
        except KeyboardInterrupt:
            exit(0)
        except:
            traceback.print_exc()
            continue

    # NEW: Call the function to generate the file lists after all processing is done
    generate_file_lists(args.preprocessed_root)

if __name__ == '__main__':
    main(args)
import os
import shutil
import subprocess
from pathlib import Path

import cv2


def _check_ffmpeg():
    if not shutil.which('ffmpeg'):
        raise EnvironmentError("ffmpeg non trovato nel PATH. Installalo e riavvia.")


def trim_video(input_path: str, output_path: str, start: float, end: float):
    """Taglia un video tra start e end (secondi) usando FFmpeg."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    if end <= start:
        raise ValueError("La fine deve essere maggiore dell'inizio")
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-ss', str(start), '-to', str(end),
        '-c', 'copy', output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path


def add_music_to_video(video_path: str, audio_path: str, output_path: str, loop: bool = False):
    """Aggiunge o sostituisce la traccia audio di un video."""
    _check_ffmpeg()
    if not Path(video_path).is_file() or not Path(audio_path).is_file():
        raise FileNotFoundError("File video o audio non trovato")
    cmd = ['ffmpeg', '-y', '-i', video_path]
    if loop:
        cmd += ['-stream_loop', '-1']
    cmd += [
        '-i', audio_path,
        '-map', '0:v:0', '-map', '1:a:0',
        '-c:v', 'copy', '-shortest', output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path


def apply_filter(input_path: str, output_path: str, filter_name: str = "grayscale"):
    """Applica un filtro FFmpeg al video."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    filters = {
        "grayscale": "format=gray",
        "blur": "boxblur=3:3",
        "negate": "negate",
        "edgedetect": "edgedetect=mode=colormix",
        "vignette": "vignette",
        "sharpen": "unsharp"
    }
    vf = filters.get(filter_name, filter_name)
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', vf, '-c:a', 'copy', output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path


def extract_frames(input_path: str, output_folder: str, interval: float = 1.0):
    """Estrae frame da un video ogni `interval` secondi."""
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError("Impossibile aprire il video")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        raise ValueError("FPS non validi")
    step = int(fps * interval)
    if step < 1:
        step = 1
    os.makedirs(output_folder, exist_ok=True)
    count = 0
    i = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if i % step == 0:
            out = os.path.join(output_folder, f"frame_{count:05d}.jpg")
            cv2.imwrite(out, frame)
            count += 1
        i += 1
    cap.release()
    return output_folder

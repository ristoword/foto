import os
import shutil
import subprocess
from pathlib import Path

import cv2


def _check_ffmpeg():
    if not shutil.which('ffmpeg'):
        raise EnvironmentError("ffmpeg non trovato nel PATH. Installalo e riavvia.")


def _run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] if result.stderr else "FFmpeg error")


def trim_video(input_path: str, output_path: str, start: float, end: float):
    """Taglia un video tra start e end (secondi) usando FFmpeg."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    if end <= start:
        raise ValueError("La fine deve essere maggiore dell'inizio")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
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
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
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
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
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


def change_speed(input_path: str, output_path: str, speed: float = 2.0):
    """Velocizza o rallenta un video. speed>1 = time-lapse, <1 = slow motion."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    if speed <= 0:
        raise ValueError("La velocità deve essere > 0")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    # video PTS and audio tempo
    atempo = speed
    atempo_filters = []
    s = atempo
    while s > 2.0:
        atempo_filters.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        atempo_filters.append("atempo=0.5")
        s *= 2.0
    atempo_filters.append(f"atempo={s:.4f}")
    audio_filter = ",".join(atempo_filters)
    vf = f"setpts={1/speed:.4f}*PTS"
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', vf,
        '-af', audio_filter,
        output_path
    ]
    _run(cmd)
    return output_path


def set_volume(input_path: str, output_path: str, volume: float = 1.0):
    """Imposta il volume dell'audio (1.0 = originale, 0 = muto, 2.0 = doppio)."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-af', f'volume={volume:.2f}',
        '-c:v', 'copy',
        output_path
    ]
    _run(cmd)
    return output_path


def extract_audio(input_path: str, output_path: str):
    """Estrae la traccia audio da un video."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = ['ffmpeg', '-y', '-i', input_path, '-vn', '-acodec', 'libmp3lame', '-q:a', '2', output_path]
    _run(cmd)
    return output_path


def add_text_overlay(
    input_path: str,
    output_path: str,
    text: str,
    position: str = "bottom",
    font_size: int = 48,
    color: str = "white",
    start_sec: float = 0,
    end_sec: float = -1,
):
    """Sovrappone testo (titolo/sottotitolo) sul video tramite FFmpeg drawtext."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pos_map = {
        "top": f"x=(w-text_w)/2:y=30",
        "bottom": f"x=(w-text_w)/2:y=h-text_h-30",
        "center": f"x=(w-text_w)/2:y=(h-text_h)/2",
        "top-left": "x=20:y=20",
        "top-right": "x=w-text_w-20:y=20",
        "bottom-left": f"x=20:y=h-text_h-20",
        "bottom-right": f"x=w-text_w-20:y=h-text_h-20",
    }
    pos_expr = pos_map.get(position, pos_map["bottom"])
    safe_text = text.replace("'", "\\'").replace(":", "\\:")
    enable = f"between(t,{start_sec},{end_sec})" if end_sec >= 0 else "1"
    font_file = ""
    for fp in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if Path(fp).exists():
            font_file = f":fontfile={fp}"
            break
    vf = (
        f"drawtext=text='{safe_text}'"
        f":fontsize={font_size}"
        f":fontcolor={color}"
        f":box=1:boxcolor=black@0.5:boxborderw=8"
        f":{pos_expr}"
        f":enable='{enable}'"
        f"{font_file}"
    )
    cmd = ['ffmpeg', '-y', '-i', input_path, '-vf', vf, '-c:a', 'copy', output_path]
    _run(cmd)
    return output_path


def video_to_gif(input_path: str, output_path: str, fps: int = 10, scale: int = 480, start: float = 0, duration: float = 10):
    """Converte un clip video in GIF animata ottimizzata."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    palette = str(Path(output_path).with_suffix('.png'))
    cmd_palette = [
        'ffmpeg', '-y', '-ss', str(start), '-t', str(duration), '-i', input_path,
        '-vf', f'fps={fps},scale={scale}:-1:flags=lanczos,palettegen',
        palette
    ]
    cmd_gif = [
        'ffmpeg', '-y', '-ss', str(start), '-t', str(duration), '-i', input_path,
        '-i', palette,
        '-lavfi', f'fps={fps},scale={scale}:-1:flags=lanczos[x];[x][1:v]paletteuse',
        output_path
    ]
    _run(cmd_palette)
    _run(cmd_gif)
    try:
        Path(palette).unlink()
    except Exception:
        pass
    return output_path


def mute_video(input_path: str, output_path: str):
    """Rimuove la traccia audio dal video."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = ['ffmpeg', '-y', '-i', input_path, '-c:v', 'copy', '-an', output_path]
    _run(cmd)
    return output_path


def get_video_info(input_path: str) -> dict:
    """Restituisce informazioni sul video (durata, dimensioni, fps, codec)."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        return {}
    info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": round(cap.get(cv2.CAP_PROP_FPS), 2),
        "frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "duration_sec": round(cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1), 2),
    }
    cap.release()
    return info


def concatenate_with_transition(input_paths: list, output_path: str, transition_duration: float = 0.5):
    """Concatena video con dissolvenza tra un clip e il successivo."""
    _check_ffmpeg()
    if len(input_paths) < 2:
        raise ValueError("Servono almeno 2 video")
    for p in input_paths:
        if not Path(p).is_file():
            raise FileNotFoundError(f"File non trovato: {p}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    inputs = []
    for p in input_paths:
        inputs += ['-i', p]
    n = len(input_paths)
    filter_parts = []
    for i in range(n):
        filter_parts.append(f"[{i}:v]format=yuv420p[v{i}]")
    xfade_parts = []
    prev = "v0"
    for i in range(1, n):
        out_label = f"vx{i}" if i < n - 1 else "vout"
        filter_parts.append(f"[{prev}][v{i}]xfade=transition=fade:duration={transition_duration}:offset=3[{out_label}]")
        prev = out_label
    filter_complex = ";".join(filter_parts)
    cmd = ['ffmpeg', '-y'] + inputs + ['-filter_complex', filter_complex, '-map', '[vout]', output_path]
    _run(cmd)
    return output_path

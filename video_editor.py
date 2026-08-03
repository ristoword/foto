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


# ---------------------------------------------------------------------------
# STRUMENTI VIDEO PROFESSIONALI
# ---------------------------------------------------------------------------

def change_speed(input_path: str, output_path: str, speed: float = 2.0):
    """Cambia la velocità del video (0.25=rallentato 4x, 2.0=veloce 2x)."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    if speed <= 0:
        raise ValueError("La velocità deve essere positiva")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    video_filter = f"setpts={1/speed}*PTS"
    audio_filter = f"atempo={speed}" if 0.5 <= speed <= 2.0 else None
    if audio_filter is None and speed > 2.0:
        parts = []
        remaining = speed
        while remaining > 2.0:
            parts.append("atempo=2.0")
            remaining /= 2.0
        parts.append(f"atempo={remaining:.4f}")
        audio_filter = ",".join(parts)
    elif audio_filter is None:
        parts = []
        remaining = speed
        while remaining < 0.5:
            parts.append("atempo=0.5")
            remaining /= 0.5
        parts.append(f"atempo={remaining:.4f}")
        audio_filter = ",".join(parts)
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-filter_complex',
        f'[0:v]{video_filter}[v];[0:a]{audio_filter}[a]',
        '-map', '[v]', '-map', '[a]',
        '-c:v', 'libx264', '-c:a', 'aac', output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path


def reverse_video(input_path: str, output_path: str, include_audio: bool = True):
    """Inverti la riproduzione del video."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if include_audio:
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-vf', 'reverse', '-af', 'areverse',
            '-c:v', 'libx264', '-c:a', 'aac', output_path,
        ]
    else:
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-vf', 'reverse', '-an',
            '-c:v', 'libx264', output_path,
        ]
    subprocess.run(cmd, check=True)
    return output_path


def add_text_overlay(input_path: str, output_path: str, text: str,
                     position: str = "center", font_size: int = 48,
                     color: str = "white", bg_color: str = "black@0.5",
                     start_time: float = 0, duration: float = None):
    """Aggiungi testo/titolo al video con posizionamento e tempistica."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    pos_map = {
        "center": "x=(w-text_w)/2:y=(h-text_h)/2",
        "top": "x=(w-text_w)/2:y=40",
        "bottom": "x=(w-text_w)/2:y=h-text_h-40",
        "top-left": "x=40:y=40",
        "top-right": "x=w-text_w-40:y=40",
        "bottom-left": "x=40:y=h-text_h-40",
        "bottom-right": "x=w-text_w-40:y=h-text_h-40",
    }
    pos = pos_map.get(position, pos_map["center"])

    escaped = text.replace("'", "\\'").replace(":", "\\:")
    drawtext = (
        f"drawtext=text='{escaped}':fontsize={font_size}:"
        f"fontcolor={color}:box=1:boxcolor={bg_color}:boxborderw=8:{pos}"
    )
    if start_time > 0 or duration is not None:
        enable_parts = []
        enable_parts.append(f"gte(t,{start_time})")
        if duration is not None:
            enable_parts.append(f"lte(t,{start_time + duration})")
        drawtext += f":enable='{'+'.join(enable_parts)}'"

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', drawtext,
        '-c:v', 'libx264', '-c:a', 'copy', output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path


def color_grade_video(input_path: str, output_path: str,
                      brightness: float = 0, contrast: float = 1.0,
                      saturation: float = 1.0, temperature: float = 0,
                      gamma: float = 1.0, exposure: float = 0):
    """Color grading professionale: luminosità, contrasto, saturazione, temperatura."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    filters = []
    if brightness != 0 or contrast != 1.0:
        filters.append(f"eq=brightness={brightness}:contrast={contrast}:gamma={gamma}")
    elif gamma != 1.0:
        filters.append(f"eq=gamma={gamma}")

    if saturation != 1.0:
        filters.append(f"hue=s={saturation}")

    if temperature != 0:
        r_shift = temperature * 0.1
        b_shift = -temperature * 0.1
        filters.append(f"colorbalance=rs={r_shift}:bs={b_shift}")

    if exposure != 0:
        ev = 2 ** exposure
        filters.append(f"curves=all='0/0 0.5/{min(1, 0.5 * ev)} 1/1'")

    if not filters:
        filters.append("null")

    vf = ",".join(filters)
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', vf, '-c:a', 'copy',
        '-c:v', 'libx264', output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path


def create_timeline(clips, output_path: str, transition: str = "fade",
                    transition_duration: float = 0.5,
                    resolution: str = "1920x1080", fps: int = 30):
    """Assembla una timeline con più clip e transizioni.

    clips: lista di dict con 'path', 'start' (opzionale), 'end' (opzionale),
           'speed' (opzionale, default 1.0)
    """
    _check_ffmpeg()
    if not clips:
        raise ValueError("Nessuna clip fornita")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    width, height = map(int, resolution.split('x'))

    inputs = []
    filter_parts = []
    n = len(clips)

    for i, clip in enumerate(clips):
        p = clip["path"]
        if not Path(p).is_file():
            raise FileNotFoundError(f"Clip non trovata: {p}")
        trim_args = []
        if clip.get("start") is not None:
            trim_args += ['-ss', str(clip["start"])]
        if clip.get("end") is not None:
            trim_args += ['-to', str(clip["end"])]
        inputs += trim_args + ['-i', p]

        speed = clip.get("speed", 1.0)
        speed_filter = f",setpts={1/speed}*PTS" if speed != 1.0 else ""
        filter_parts.append(
            f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"fps={fps},format=yuv420p{speed_filter}[v{i}]"
        )

    if n == 1:
        cmd = ['ffmpeg', '-y'] + inputs + [
            '-filter_complex', ';'.join(filter_parts) + f';[v0]null[outv]',
            '-map', '[outv]', '-map', '0:a?',
            '-c:v', 'libx264', '-c:a', 'aac', '-shortest', output_path,
        ]
    else:
        current = "[v0]"
        timeline_pos = 0
        for i, clip in enumerate(clips):
            p = clip["path"]
            dur_cmd = ['ffprobe', '-v', 'error', '-show_entries',
                       'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', p]
            try:
                dur = float(subprocess.check_output(dur_cmd, text=True).strip())
            except Exception:
                dur = 10.0
            start = clip.get("start", 0) or 0
            end = clip.get("end", dur) or dur
            clip_dur = (end - start) / clip.get("speed", 1.0)
            if i > 0:
                offset = max(0, timeline_pos - transition_duration)
                next_label = "[outv]" if i == n - 1 else f"[tmp{i}]"
                tr = transition if transition in ("fade", "wipeleft", "wiperight",
                     "wipeup", "wipedown", "slideleft", "slideright",
                     "dissolve", "pixelize", "circleopen") else "fade"
                filter_parts.append(
                    f"{current}[v{i}]xfade=transition={tr}:"
                    f"duration={transition_duration}:offset={offset:.3f}{next_label}"
                )
                current = next_label
            timeline_pos += clip_dur

        if current != "[outv]":
            filter_parts.append(f"{current}null[outv]")

        cmd = ['ffmpeg', '-y'] + inputs + [
            '-filter_complex', ';'.join(filter_parts),
            '-map', '[outv]', '-an',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', output_path,
        ]

    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg errore: {result.stderr[-500:]}")
    return output_path


def add_fade(input_path: str, output_path: str,
             fade_in: float = 0, fade_out: float = 0,
             audio_fade_in: float = 0, audio_fade_out: float = 0):
    """Aggiungi dissolvenza in apertura/chiusura (video e audio)."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    dur_cmd = ['ffprobe', '-v', 'error', '-show_entries',
               'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
               input_path]
    try:
        total = float(subprocess.check_output(dur_cmd, text=True).strip())
    except Exception:
        total = 30.0

    v_filters = []
    a_filters = []
    if fade_in > 0:
        v_filters.append(f"fade=t=in:st=0:d={fade_in}")
    if fade_out > 0:
        v_filters.append(f"fade=t=out:st={total - fade_out:.3f}:d={fade_out}")
    if audio_fade_in > 0:
        a_filters.append(f"afade=t=in:st=0:d={audio_fade_in}")
    if audio_fade_out > 0:
        a_filters.append(f"afade=t=out:st={total - audio_fade_out:.3f}:d={audio_fade_out}")

    cmd = ['ffmpeg', '-y', '-i', input_path]
    if v_filters:
        cmd += ['-vf', ','.join(v_filters)]
    if a_filters:
        cmd += ['-af', ','.join(a_filters)]
    cmd += ['-c:v', 'libx264', '-c:a', 'aac', output_path]
    subprocess.run(cmd, check=True)
    return output_path


def picture_in_picture(main_path: str, overlay_path: str, output_path: str,
                       position: str = "bottom-right", scale: float = 0.25,
                       start_time: float = 0, duration: float = None):
    """Sovrapponi un video PiP (picture-in-picture)."""
    _check_ffmpeg()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pos_map = {
        "top-left": "20:20",
        "top-right": "main_w-overlay_w-20:20",
        "bottom-left": "20:main_h-overlay_h-20",
        "bottom-right": "main_w-overlay_w-20:main_h-overlay_h-20",
        "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2",
    }
    pos = pos_map.get(position, pos_map["bottom-right"])
    overlay_filter = f"[1:v]scale=iw*{scale}:ih*{scale}[pip]"
    main_filter = f"[0:v][pip]overlay={pos}"
    if start_time > 0 or duration is not None:
        enable = f":enable='between(t,{start_time},{start_time + (duration or 9999)})'"
        main_filter += enable

    cmd = [
        'ffmpeg', '-y', '-i', main_path, '-i', overlay_path,
        '-filter_complex', f'{overlay_filter};{main_filter}',
        '-c:v', 'libx264', '-c:a', 'copy', '-shortest', output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path


def chroma_key(input_path: str, background_path: str, output_path: str,
               color: str = "green", similarity: float = 0.3,
               blend: float = 0.05):
    """Rimuovi sfondo verde/blu (chroma key) e sostituisci con altro video/immagine."""
    _check_ffmpeg()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    hex_colors = {"green": "00FF00", "blue": "0000FF", "red": "FF0000"}
    key_color = hex_colors.get(color, color)
    cmd = [
        'ffmpeg', '-y', '-i', input_path, '-i', background_path,
        '-filter_complex',
        f'[0:v]colorkey=0x{key_color}:similarity={similarity}:blend={blend}[fg];'
        f'[1:v][fg]overlay=shortest=1',
        '-c:v', 'libx264', '-c:a', 'copy', output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path


def adjust_volume(input_path: str, output_path: str, volume: float = 1.0):
    """Regola il volume audio del video (1.0 = originale, 2.0 = doppio)."""
    _check_ffmpeg()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-af', f'volume={volume}',
        '-c:v', 'copy', '-c:a', 'aac', output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path


def stabilize_video(input_path: str, output_path: str, smoothing: int = 10):
    """Stabilizza un video tremolante con vidstab (se disponibile) o deshake."""
    _check_ffmpeg()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', f'deshake=rx=32:ry=32',
        '-c:v', 'libx264', '-c:a', 'copy', output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path


def add_video_watermark(input_path: str, output_path: str,
                        text: str = "AppFoto Studio",
                        position: str = "bottom-right",
                        font_size: int = 24, opacity: float = 0.5):
    """Aggiungi watermark di testo al video."""
    _check_ffmpeg()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pos_map = {
        "top-left": "x=20:y=20",
        "top-right": "x=w-text_w-20:y=20",
        "bottom-left": "x=20:y=h-text_h-20",
        "bottom-right": "x=w-text_w-20:y=h-text_h-20",
        "center": "x=(w-text_w)/2:y=(h-text_h)/2",
    }
    pos = pos_map.get(position, pos_map["bottom-right"])
    escaped = text.replace("'", "\\'").replace(":", "\\:")
    alpha = min(1, max(0, opacity))
    drawtext = (
        f"drawtext=text='{escaped}':fontsize={font_size}:"
        f"fontcolor=white@{alpha}:{pos}"
    )
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', drawtext, '-c:v', 'libx264', '-c:a', 'copy', output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path


def extract_audio(input_path: str, output_path: str):
    """Estrai la traccia audio da un video."""
    _check_ffmpeg()
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"File non trovato: {input_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vn', '-c:a', 'libmp3lame', '-q:a', '2', output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path


def get_video_info(input_path: str) -> dict:
    """Ottieni informazioni tecniche sul video."""
    if not Path(input_path).is_file():
        return {}
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', input_path,
    ]
    try:
        result = subprocess.check_output(cmd, text=True)
        import json
        data = json.loads(result)
        info = {"file": Path(input_path).name}
        fmt = data.get("format", {})
        info["durata"] = f"{float(fmt.get('duration', 0)):.1f}s"
        info["dimensione"] = f"{int(fmt.get('size', 0)) / (1024*1024):.1f} MB"
        info["bitrate"] = f"{int(fmt.get('bit_rate', 0)) / 1000:.0f} kbps"
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                info["codec_video"] = s.get("codec_name", "?")
                info["risoluzione"] = f"{s.get('width', '?')}x{s.get('height', '?')}"
                r = s.get("r_frame_rate", "0/1").split("/")
                info["fps"] = f"{int(r[0]) / max(1, int(r[1])):.1f}" if len(r) == 2 else "?"
            elif s.get("codec_type") == "audio":
                info["codec_audio"] = s.get("codec_name", "?")
                info["canali"] = s.get("channels", "?")
                info["sample_rate"] = f"{s.get('sample_rate', '?')} Hz"
        return info
    except Exception:
        return {"file": Path(input_path).name, "errore": "Impossibile leggere info"}

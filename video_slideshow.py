"""Slideshow professionale stile iMovie / Canva / CapCut / Adobe Express."""
import os
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

from PIL import Image


TRANSITIONS = {
    "dissolvenza": "fade",
    "dissolvi": "dissolve",
    "wipe sinistra": "wipeleft",
    "wipe destra": "wiperight",
    "wipe su": "wipeup",
    "wipe giu": "wipedown",
    "slide sinistra": "slideleft",
    "slide destra": "slideright",
    "cerchio": "circleopen",
    "pixel": "pixelize",
    "nessuna": "none",
}

FILTERS = {
    "nessuno": None,
    "bianco e nero": "hue=s=0",
    "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
    "vivace": "eq=saturation=1.4:contrast=1.1",
    "cinema": "eq=contrast=1.15:brightness=-0.03:saturation=0.85,curves=vintage",
    "caldo": "colorbalance=rs=0.12:gs=0.02:bs=-0.08",
    "freddo": "colorbalance=rs=-0.08:bs=0.12",
    "vintage": "eq=saturation=0.7:contrast=1.1,curves=vintage",
    "soft": "eq=contrast=0.95:brightness=0.05,gblur=sigma=0.4",
    "contrasto alto": "eq=contrast=1.35:saturation=1.1",
}

TEMPLATES = {
    "iMovie classico": {
        "duration": 3.5,
        "transition": "dissolvenza",
        "transition_dur": 0.8,
        "filter": "nessuno",
        "ken_burns": True,
        "music_volume": 0.7,
        "fade_audio": 1.5,
        "aspect": "16:9",
        "style": "imovie",
    },
    "Canva Social": {
        "duration": 2.5,
        "transition": "slide sinistra",
        "transition_dur": 0.5,
        "filter": "vivace",
        "ken_burns": False,
        "music_volume": 0.8,
        "fade_audio": 1.0,
        "aspect": "1:1",
        "style": "canva",
    },
    "CapCut Reels": {
        "duration": 2.0,
        "transition": "wipe sinistra",
        "transition_dur": 0.35,
        "filter": "contrasto alto",
        "ken_burns": True,
        "music_volume": 1.0,
        "fade_audio": 0.5,
        "aspect": "9:16",
        "style": "capcut",
    },
    "Adobe Express": {
        "duration": 3.0,
        "transition": "cerchio",
        "transition_dur": 0.6,
        "filter": "caldo",
        "ken_burns": False,
        "music_volume": 0.75,
        "fade_audio": 1.2,
        "aspect": "16:9",
        "style": "adobe",
    },
    "CapCut TikTok": {
        "duration": 1.8,
        "transition": "pixel",
        "transition_dur": 0.3,
        "filter": "vivace",
        "ken_burns": True,
        "music_volume": 1.0,
        "fade_audio": 0.4,
        "aspect": "9:16",
        "style": "capcut",
    },
    "iMovie Film": {
        "duration": 4.0,
        "transition": "dissolvi",
        "transition_dur": 1.0,
        "filter": "cinema",
        "ken_burns": True,
        "music_volume": 0.6,
        "fade_audio": 2.0,
        "aspect": "16:9",
        "style": "imovie",
    },
}

ASPECT_RESOLUTIONS = {
    "16:9": {"1920x1080": (1920, 1080), "1280x720": (1280, 720), "3840x2160": (3840, 2160)},
    "9:16": {"1080x1920": (1080, 1920), "720x1280": (720, 1280)},
    "1:1": {"1080x1080": (1080, 1080), "720x720": (720, 720)},
    "4:5": {"1080x1350": (1080, 1350)},
}


def _list_images(folder: str) -> List[str]:
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}
    return sorted([str(p.resolve()) for p in Path(folder).iterdir()
                   if p.suffix.lower() in exts and p.is_file()])


def _escape_drawtext(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
    )


def _normalize_image(path: str, width: int, height: int, fit: str = "contain") -> str:
    """Pad/scale an image to the target resolution and save to a temp file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Foto non trovata o non apribile: {path}")
    try:
        with Image.open(p) as img:
            img.load()
            if img.mode != "RGB":
                img = img.convert("RGB")
            if fit == "cover":
                ratio = max(width / img.width, height / img.height)
                nw, nh = int(img.width * ratio), int(img.height * ratio)
                img = img.resize((nw, nh), Image.Resampling.LANCZOS)
                left = (nw - width) // 2
                top = (nh - height) // 2
                img = img.crop((left, top, left + width, top + height))
                new_img = img
            else:
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                new_img = Image.new("RGB", (width, height), (0, 0, 0))
                offset = ((width - img.width) // 2, (height - img.height) // 2)
                new_img.paste(img, offset)
            fd, tmp = tempfile.mkstemp(suffix=".jpg")
            os.close(fd)
            new_img.save(tmp, quality=95)
    except FileNotFoundError:
        raise
    except Exception as e:
        raise ValueError(f"Impossibile aprire la foto '{p.name}': {e}") from e
    return tmp


def _ken_burns_filter(i: int, duration: float, width: int, height: int, zoom_in: bool = True) -> str:
    """Effetto Ken Burns stile iMovie (zoom lento + pan)."""
    frames = max(int(duration * 30), 1)
    if zoom_in:
        return (
            f"[{i}:v]scale={int(width*1.25)}:{int(height*1.25)},"
            f"zoompan=z='min(zoom+0.0015,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={width}x{height}:fps=30,format=yuv420p,setsar=1[v{i}]"
        )
    return (
        f"[{i}:v]scale={int(width*1.25)}:{int(height*1.25)},"
        f"zoompan=z='if(eq(on,1),1.2,max(1.0,zoom-0.0015))':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={width}x{height}:fps=30,format=yuv420p,setsar=1[v{i}]"
    )


def make_slideshow(
    input_paths: List[str],
    output: str,
    duration: float = 3.0,
    transition: float = 0.5,
    resolution: str = "1920x1080",
    fps: int = 30,
    music: Optional[str] = None,
    transition_type: str = "fade",
    filter_name: Optional[str] = None,
    ken_burns: bool = False,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    title_position: str = "center",
    music_volume: float = 0.8,
    fade_audio: float = 1.0,
    fit: str = "contain",
) -> str:
    """Crea slideshow stile iMovie/Canva/CapCut/Adobe Express."""
    if not input_paths:
        raise ValueError("Nessuna immagine fornita per lo slideshow")
    if not shutil.which("ffmpeg"):
        raise EnvironmentError("ffmpeg non trovato nel PATH. Installalo e riavvia.")

    valid = []
    for raw in input_paths:
        p = Path(str(raw).strip())
        if not p.is_file():
            raise FileNotFoundError(f"Foto non trovata: {raw}")
        valid.append(str(p.resolve()))
    input_paths = valid

    if transition >= duration:
        transition = max(0.0, duration * 0.3)

    # mappa nome UI -> filtro ffmpeg
    xfade = TRANSITIONS.get(transition_type, transition_type)
    if xfade not in (
        "fade", "dissolve", "wipeleft", "wiperight", "wipeup", "wipedown",
        "slideleft", "slideright", "circleopen", "pixelize", "none",
    ):
        xfade = "fade"

    vf_filter = FILTERS.get(filter_name) if filter_name else None
    if filter_name and filter_name not in FILTERS and filter_name not in (None, "nessuno"):
        # se passato direttamente un filtro ffmpeg
        vf_filter = filter_name if filter_name != "nessuno" else None

    width, height = map(int, resolution.split("x"))
    n = len(input_paths)
    total_duration = (n * duration) - ((n - 1) * (transition if xfade != "none" else 0))

    normalized = []
    try:
        normalized = [_normalize_image(p, width, height, fit=fit) for p in input_paths]

        inputs = []
        for p in normalized:
            inputs.extend(["-loop", "1", "-t", str(duration), "-i", p])

        music_index = None
        if music and Path(music).is_file():
            music_index = n
            inputs += ["-stream_loop", "-1", "-i", str(Path(music).resolve())]

        # Prepara stream video per ogni foto
        prep = []
        for i in range(n):
            if ken_burns:
                prep.append(_ken_burns_filter(i, duration, width, height, zoom_in=(i % 2 == 0)))
            else:
                prep.append(f"[{i}:v]format=yuv420p,fps={fps},setsar=1[v{i}]")
        filter_parts = [";".join(prep)]

        # Concatena con transizioni
        if n == 1 or xfade == "none":
            if n == 1:
                filter_parts.append("[v0]format=yuv420p[vout]")
            else:
                concat_in = "".join(f"[v{i}]" for i in range(n))
                filter_parts.append(f"{concat_in}concat=n={n}:v=1:a=0[vout]")
                total_duration = n * duration
        else:
            current = "[v0]"
            timeline = duration
            for i in range(1, n):
                offset = max(0.0, timeline - transition)
                next_label = "[vout]" if i == n - 1 else f"[tmp{i}]"
                filter_parts.append(
                    f"{current}[v{i}]xfade=transition={xfade}:"
                    f"duration={transition}:offset={offset:.3f}{next_label}"
                )
                current = next_label
                timeline += duration - transition
            if current != "[vout]":
                filter_parts.append(f"{current}format=yuv420p[vout]")

        # Filtri look (CapCut / Adobe Express)
        last = "[vout]"
        if vf_filter:
            filter_parts.append(f"{last}{vf_filter}[vfilt]")
            last = "[vfilt]"

        # Titoli stile Canva / iMovie / Adobe Express
        if title or subtitle:
            draw = []
            pos_map = {
                "center": ("(w-text_w)/2", "(h-text_h)/2"),
                "top": ("(w-text_w)/2", "60"),
                "bottom": ("(w-text_w)/2", "h-text_h-80"),
            }
            tx, ty = pos_map.get(title_position, pos_map["center"])
            if title:
                t = _escape_drawtext(title)
                draw.append(
                    f"drawtext=text='{t}':fontsize={max(36, width // 28)}:"
                    f"fontcolor=white:borderw=3:bordercolor=black@0.6:"
                    f"x={tx}:y={ty}:enable='between(t,0,{min(4.0, total_duration)})'"
                )
            if subtitle:
                s = _escape_drawtext(subtitle)
                sub_y = f"h-text_h-50" if title_position != "bottom" else "h-text_h-120"
                draw.append(
                    f"drawtext=text='{s}':fontsize={max(22, width // 45)}:"
                    f"fontcolor=white@0.9:borderw=2:bordercolor=black@0.5:"
                    f"x=(w-text_w)/2:y={sub_y}:enable='between(t,0,{min(4.0, total_duration)})'"
                )
            filter_parts.append(f"{last}{','.join(draw)}[vfinal]")
            last = "[vfinal]"
        else:
            filter_parts.append(f"{last}format=yuv420p[vfinal]")
            last = "[vfinal]"

        # Fade video in/out
        if fade_audio > 0:
            fi = min(fade_audio, total_duration / 3)
            fo = min(fade_audio, total_duration / 3)
            fo_start = max(0, total_duration - fo)
            filter_parts.append(
                f"{last}fade=t=in:st=0:d={fi},fade=t=out:st={fo_start:.3f}:d={fo}[voutfade]"
            )
            map_v = "[voutfade]"
        else:
            map_v = last

        Path(output).parent.mkdir(parents=True, exist_ok=True)

        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", ";".join(filter_parts),
            "-map", map_v,
        ]

        if music_index is not None:
            vol = max(0.0, min(2.0, float(music_volume)))
            af = [f"volume={vol}"]
            if fade_audio > 0:
                fi = min(fade_audio, total_duration / 3)
                fo = min(fade_audio, total_duration / 3)
                fo_start = max(0, total_duration - fo)
                af.append(f"afade=t=in:st=0:d={fi}")
                af.append(f"afade=t=out:st={fo_start:.3f}:d={fo}")
            # usa -filter:a separato mappando audio
            cmd += [
                "-map", f"{music_index}:a",
                "-filter:a", ",".join(af),
                "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-t", str(total_duration),
            ]
        else:
            cmd += ["-an"]

        cmd += [
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(output),
        ]

        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "errore sconosciuto")[-1000:]
            raise RuntimeError(f"ffmpeg ha fallito:\n{err}")
    finally:
        for p in normalized:
            try:
                os.remove(p)
            except OSError:
                pass

    return output


def apply_template(name: str) -> Dict[str, Any]:
    """Restituisce i parametri di un template iMovie/Canva/CapCut/Adobe Express."""
    return dict(TEMPLATES.get(name, TEMPLATES["iMovie classico"]))


def main():
    parser = argparse.ArgumentParser(description="Create a slideshow from images.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--transition", type=float, default=0.5)
    parser.add_argument("--resolution", default="1920x1080")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--music", default=None)
    args = parser.parse_args()
    paths = _list_images(args.input) if Path(args.input).is_dir() else args.input.split(",")
    make_slideshow(paths, args.output, args.duration, args.transition,
                   args.resolution, args.fps, args.music)
    print(f"Slideshow saved to {args.output}")


if __name__ == "__main__":
    main()

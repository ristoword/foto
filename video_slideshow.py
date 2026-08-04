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

# Filtri stabili (niente curves=vintage: fallisce su molti build FFmpeg)
FILTERS = {
    "nessuno": None,
    "bianco e nero": "hue=s=0",
    "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
    "vivace": "eq=saturation=1.35:contrast=1.08",
    "cinema": "eq=contrast=1.12:brightness=-0.04:saturation=0.82",
    "caldo": "colorbalance=rs=0.1:gs=0.02:bs=-0.08",
    "freddo": "colorbalance=rs=-0.08:bs=0.1",
    "vintage": "eq=saturation=0.72:contrast=1.08:gamma=1.05",
    "soft": "eq=contrast=0.95:brightness=0.04",
    "contrasto alto": "eq=contrast=1.3:saturation=1.08",
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
        "transition": "dissolvenza",
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

SAFE_XFADE = {
    "fade", "dissolve", "wipeleft", "wiperight", "wipeup", "wipedown",
    "slideleft", "slideright", "circleopen", "pixelize", "none",
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
        .replace(",", "\\,")
    )


def _find_font() -> Optional[str]:
    """Trova un font TrueType utilizzabile da drawtext."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for c in candidates:
        if Path(c).is_file():
            return c.replace("\\", "/").replace(":", "\\:")
    return None


def _even(n: int) -> int:
    return n if n % 2 == 0 else n - 1


def _normalize_image(path: str, width: int, height: int, fit: str = "contain") -> str:
    """Pad/scale an image to the target resolution and save as JPEG RGB."""
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
                new_img = img.crop((left, top, left + width, top + height))
            else:
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                new_img = Image.new("RGB", (width, height), (0, 0, 0))
                offset = ((width - img.width) // 2, (height - img.height) // 2)
                new_img.paste(img, offset)
            fd, tmp = tempfile.mkstemp(suffix=".jpg")
            os.close(fd)
            new_img.save(tmp, quality=92, subsampling=0)
    except FileNotFoundError:
        raise
    except Exception as e:
        raise ValueError(f"Impossibile aprire la foto '{p.name}': {e}") from e
    return tmp


def _run_ffmpeg(cmd: List[str], cwd: Optional[str] = None) -> None:
    result = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "errore sconosciuto")[-1200:]
        raise RuntimeError(f"ffmpeg ha fallito:\n{err}")


def _make_clip(
    image_path: str,
    clip_path: str,
    duration: float,
    fps: int,
    width: int,
    height: int,
    ken_burns: bool = False,
    zoom_in: bool = True,
) -> str:
    """Crea un clip video singolo (più affidabile di zoompan+xfade nello stesso grafo)."""
    nframes = max(int(round(duration * fps)), 1)
    if ken_burns:
        # scala a 1.25x e zoom lento — dimensioni uscite fisse e pari
        sw, sh = _even(int(width * 1.25)), _even(int(height * 1.25))
        if zoom_in:
            zexpr = "min(1.0+0.0012*on,1.2)"
        else:
            zexpr = "if(eq(on,1),1.2,max(1.0,1.2-0.0012*on))"
        vf = (
            f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
            f"crop={sw}:{sh},"
            f"zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={nframes}:s={width}x{height}:fps={fps},"
            f"format=yuv420p,setsar=1"
        )
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-i", image_path,
            "-vf", vf,
            "-frames:v", str(nframes),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-an",
            clip_path,
        ]
    else:
        vf = (
            f"scale={width}:{height}:flags=lanczos,"
            f"setsar=1,fps={fps},format=yuv420p"
        )
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-t", f"{duration:.3f}", "-i", image_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-an",
            clip_path,
        ]
    _run_ffmpeg(cmd)
    return clip_path


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
    """Crea slideshow stile iMovie/Canva/CapCut/Adobe Express (pipeline a 2 passi stabile)."""
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

    duration = float(duration)
    transition = float(transition)
    fps = int(fps) if fps else 30
    if transition >= duration:
        transition = max(0.05, duration * 0.25)

    xfade = TRANSITIONS.get(transition_type, transition_type)
    if xfade not in SAFE_XFADE:
        xfade = "fade"
    # pixelize è instabile su alcuni build — fallback a fade
    if xfade == "pixelize":
        xfade = "fade"

    vf_filter = None
    if filter_name and filter_name not in (None, "nessuno"):
        vf_filter = FILTERS.get(filter_name, None)
        if vf_filter is None and filter_name in FILTERS:
            vf_filter = None
        elif filter_name not in FILTERS:
            # ignora filtri sconosciuti/instabili
            vf_filter = None

    width, height = map(int, resolution.split("x"))
    width, height = _even(width), _even(height)
    n = len(input_paths)

    if xfade == "none" or n == 1:
        total_duration = n * duration
    else:
        total_duration = (n * duration) - ((n - 1) * transition)

    tmp_dir = tempfile.mkdtemp(prefix="sld_")
    normalized: List[str] = []
    clips: List[str] = []
    try:
        # 1) Normalizza foto
        normalized = [_normalize_image(p, width, height, fit=fit) for p in input_paths]

        # 2) Crea clip video singoli (Ken Burns qui, non nel grafo xfade)
        for i, img in enumerate(normalized):
            clip = os.path.join(tmp_dir, f"clip_{i:03d}.mp4")
            _make_clip(
                img, clip, duration, fps, width, height,
                ken_burns=ken_burns, zoom_in=(i % 2 == 0),
            )
            clips.append(clip)

        # 3) Assembla clip con xfade / concat
        inputs: List[str] = []
        for c in clips:
            inputs += ["-i", c]

        music_path = None
        music_index = None
        if music and Path(music).is_file():
            music_path = str(Path(music).resolve())
            music_index = len(clips)
            inputs += ["-stream_loop", "-1", "-i", music_path]

        filter_parts: List[str] = []

        if n == 1 or xfade == "none":
            if n == 1:
                filter_parts.append("[0:v]format=yuv420p,setsar=1[vout]")
            else:
                concat_in = "".join(f"[{i}:v]" for i in range(n))
                filter_parts.append(f"{concat_in}concat=n={n}:v=1:a=0,format=yuv420p,setsar=1[vout]")
                total_duration = n * duration
        else:
            # normalizza ogni clip prima di xfade
            for i in range(n):
                filter_parts.append(
                    f"[{i}:v]fps={fps},format=yuv420p,setsar=1,scale={width}:{height}[v{i}]"
                )
            current = "[v0]"
            timeline = duration
            for i in range(1, n):
                offset = max(0.0, timeline - transition)
                next_label = "[vout]" if i == n - 1 else f"[tmp{i}]"
                filter_parts.append(
                    f"{current}[v{i}]xfade=transition={xfade}:"
                    f"duration={transition:.3f}:offset={offset:.3f}{next_label}"
                )
                current = next_label
                timeline += duration - transition
            if current != "[vout]":
                filter_parts.append(f"{current}format=yuv420p,setsar=1[vout]")

        last = "[vout]"

        # Look / filtro colore
        if vf_filter:
            filter_parts.append(f"{last}{vf_filter},format=yuv420p[vfilt]")
            last = "[vfilt]"

        # Titoli — font locale nella tmp (path relativo, niente problemi con C:)
        if title or subtitle:
            font_src = None
            for c in [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
            ]:
                if Path(c).is_file():
                    font_src = c
                    break
            font_name = None
            if font_src:
                font_name = "font.ttf"
                try:
                    shutil.copy2(font_src, os.path.join(tmp_dir, font_name))
                except Exception:
                    font_name = None
            if font_name:
                pos_map = {
                    "center": ("(w-text_w)/2", "(h-text_h)/2"),
                    "top": ("(w-text_w)/2", "80"),
                    "bottom": ("(w-text_w)/2", "h-th-80"),
                }
                tx, ty = pos_map.get(title_position, pos_map["center"])
                cur = last
                if title:
                    t = _escape_drawtext(title)
                    filter_parts.append(
                        f"{cur}drawtext=fontfile={font_name}:text='{t}':"
                        f"fontsize={max(32, width // 28)}:fontcolor=white:"
                        f"x={tx}:y={ty}:box=1:boxcolor=black@0.45:boxborderw=8[t0]"
                    )
                    cur = "[t0]"
                if subtitle:
                    s = _escape_drawtext(subtitle)
                    filter_parts.append(
                        f"{cur}drawtext=fontfile={font_name}:text='{s}':"
                        f"fontsize={max(20, width // 45)}:fontcolor=white:"
                        f"x=(w-text_w)/2:y=h-th-50:box=1:boxcolor=black@0.35:boxborderw=6[t1]"
                    )
                    cur = "[t1]"
                filter_parts.append(f"{cur}format=yuv420p[vtext]")
                last = "[vtext]"

        # Fade video
        fi = fo = 0.0
        if fade_audio and fade_audio > 0 and total_duration > 0.5:
            fi = min(float(fade_audio), total_duration / 4)
            fo = min(float(fade_audio), total_duration / 4)
            fo_start = max(0.0, total_duration - fo)
            filter_parts.append(
                f"{last}fade=t=in:st=0:d={fi:.3f},fade=t=out:st={fo_start:.3f}:d={fo:.3f},format=yuv420p[vfinal]"
            )
            last = "[vfinal]"
        else:
            filter_parts.append(f"{last}format=yuv420p[vfinal]")
            last = "[vfinal]"

        # Audio nel filter_complex (evita conflitti con -filter:a)
        map_args = ["-map", last]
        if music_index is not None:
            vol = max(0.05, min(2.0, float(music_volume)))
            a_parts = [f"[{music_index}:a]volume={vol}"]
            if fi > 0:
                a_parts.append(f"afade=t=in:st=0:d={fi:.3f}")
            if fo > 0:
                fo_start = max(0.0, total_duration - fo)
                a_parts.append(f"afade=t=out:st={fo_start:.3f}:d={fo:.3f}")
            a_parts.append(f"atrim=0:{total_duration:.3f}")
            a_parts.append("asetpts=PTS-STARTPTS")
            filter_parts.append(",".join(a_parts) + "[aout]")
            map_args += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
        else:
            map_args += ["-an"]

        Path(output).parent.mkdir(parents=True, exist_ok=True)
        cmd = (
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
            + inputs
            + ["-filter_complex", ";".join(filter_parts)]
            + map_args
            + [
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-r", str(fps),
                "-t", f"{total_duration:.3f}",
                "-movflags", "+faststart",
                str(output),
            ]
        )
        _run_ffmpeg(cmd, cwd=tmp_dir)
    finally:
        for p in normalized + clips:
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
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

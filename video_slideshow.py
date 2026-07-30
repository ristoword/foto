import os
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from PIL import Image


VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv'}


def _list_images(folder: str) -> List[str]:
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}
    return sorted([str(p) for p in Path(folder).iterdir()
                   if p.suffix.lower() in exts and p.is_file()])


def _normalize_image(path: str, width: int, height: int) -> str:
    """Pad/scale an image to the target resolution and save to a temp file."""
    with Image.open(path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        new_img = Image.new('RGB', (width, height), (0, 0, 0))
        offset = ((width - img.width) // 2, (height - img.height) // 2)
        new_img.paste(img, offset)
        fd, tmp = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        new_img.save(tmp, quality=95)
    return tmp


def make_slideshow(input_paths: List[str], output: str, duration: float = 3.0,
                   transition: float = 0.5, resolution: str = '1920x1080',
                   fps: int = 30, music: Optional[str] = None) -> str:
    """Build a slideshow video with crossfade transitions via FFmpeg."""
    if not input_paths:
        raise ValueError("No input images provided")
    if not shutil.which('ffmpeg'):
        raise EnvironmentError("ffmpeg binary not found in PATH")

    width, height = map(int, resolution.split('x'))
    normalized = [_normalize_image(p, width, height) for p in input_paths]

    # Prepare per-image video streams with the requested duration.
    # Use FFmpeg's xfade filter for crossfade.
    inputs = []
    for p in normalized:
        inputs.extend(['-loop', '1', '-t', str(duration), '-i', p])

    music_index = None
    if music and Path(music).is_file():
        music_index = len(normalized)
        inputs += ['-stream_loop', '-1', '-i', str(music)]

    filter_parts = []
    filter_parts.append(
        ";".join(f"[{i}:v]format=yuv420p,fps={fps},setsar=1[v{i}]" for i in range(len(normalized)))
    )

    current = "[v0]"
    out_label = "[outv]"
    timeline = duration
    for i in range(1, len(normalized)):
        offset = max(0.0, timeline - transition)
        next_label = out_label if i == len(normalized) - 1 else f"[tmp{i}]"
        filter_parts.append(
            f"{current}[v{i}]xfade=transition=fade:duration={transition}:offset={offset:.3f}{next_label}"
        )
        current = next_label
        timeline += duration - transition

    if current != out_label:
        filter_parts.append(f"{current}format=yuv420p{out_label}")

    cmd = ['ffmpeg', '-y'] + inputs + ['-filter_complex', ';'.join(filter_parts), '-map', out_label]

    if music_index is not None:
        total_duration = (len(normalized) * duration) - ((len(normalized) - 1) * transition)
        cmd += ['-map', f'{music_index}:a', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-t', str(total_duration)]
    else:
        cmd += ['-an']

    cmd += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', output]

    subprocess.run(cmd, check=True)

    for p in normalized:
        os.remove(p)

    return output


def main():
    parser = argparse.ArgumentParser(description="Create a slideshow from images.")
    parser.add_argument("--input", required=True, help="Folder or comma-separated image paths")
    parser.add_argument("--output", required=True, help="Output video file")
    parser.add_argument("--duration", type=float, default=3.0, help="Seconds per image")
    parser.add_argument("--transition", type=float, default=0.5, help="Fade transition duration")
    parser.add_argument("--resolution", default="1920x1080")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--music", default=None, help="Optional background music path")
    args = parser.parse_args()

    paths = _list_images(args.input) if Path(args.input).is_dir() else args.input.split(',')
    make_slideshow(paths, args.output, args.duration, args.transition,
                   args.resolution, args.fps, args.music)
    print(f"Slideshow saved to {args.output}")


if __name__ == "__main__":
    main()

import os
import argparse
import shutil
import subprocess
from pathlib import Path
from typing import List


VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}


def _is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS and path.is_file()


def _list_videos(folder: str) -> List[str]:
    return sorted([str(p) for p in Path(folder).iterdir() if _is_video(p)])


def merge_videos(input_paths: List[str], output: str, resolution: str = '1920x1080',
                 fps: int = 30) -> str:
    """Concatenate multiple video clips, normalizing resolution and framerate."""
    if not input_paths:
        raise ValueError("No input videos provided")
    if not shutil.which('ffmpeg'):
        raise EnvironmentError("ffmpeg binary not found in PATH")

    width, height = map(int, resolution.split('x'))
    inputs = []
    for p in input_paths:
        inputs.extend(['-i', p])

    n = len(input_paths)
    v_pads = [f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
              f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p[v{i}]"
              for i in range(n)]
    a_pads = [f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a{i}]"
              for i in range(n)]
    concat_input = ''.join(f"[v{i}][a{i}]" for i in range(n))
    concat = f"{concat_input}concat=n={n}:v=1:a=1[outv][outa]"

    filter_complex = ';'.join(v_pads + a_pads + [concat])

    cmd = ['ffmpeg', '-y'] + inputs + [
        '-filter_complex', filter_complex,
        '-map', '[outv]', '-map', '[outa]',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k',
        output
    ]

    subprocess.run(cmd, check=True)
    return output


def main():
    parser = argparse.ArgumentParser(description="Merge multiple video clips into one.")
    parser.add_argument("--input", required=True, help="Folder or comma-separated video paths")
    parser.add_argument("--output", required=True, help="Output merged video file")
    parser.add_argument("--resolution", default="1920x1080")
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()

    paths = _list_videos(args.input) if Path(args.input).is_dir() else args.input.split(',')
    merge_videos(paths, args.output, args.resolution, args.fps)
    print(f"Merged video saved to {args.output}")


if __name__ == "__main__":
    main()

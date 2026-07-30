import argparse
import sys
from pathlib import Path

import duplicate_finder
import photo_enhancer
import video_slideshow
import video_merger


def main():
    parser = argparse.ArgumentParser(
        description="AppFoto prototype - manage photos and videos"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Duplicate finder
    dup = sub.add_parser("duplicates", help="Find duplicate images")
    dup.add_argument("folder", help="Folder to scan")
    dup.add_argument("--threshold", type=int, default=10)
    dup.add_argument("--delete", action="store_true", help="Keep only highest-resolution copy")
    dup.add_argument("--output", default="duplicates_report.json")
    dup.add_argument("--quick", action="store_true")

    # Photo enhancer
    enh = sub.add_parser("enhance", help="Enhance photos")
    enh.add_argument("--input", required=True, help="Image or folder")
    enh.add_argument("--output", required=True, help="Output image or folder")
    enh.add_argument("--gamma", type=float, default=1.2)
    enh.add_argument("--sharp", type=float, default=1.0)
    enh.add_argument("--blur-threshold", type=float, default=100.0)

    # Slideshow
    sld = sub.add_parser("slideshow", help="Create video slideshow from images")
    sld.add_argument("--input", required=True, help="Images folder or comma-separated paths")
    sld.add_argument("--output", required=True)
    sld.add_argument("--duration", type=float, default=3.0)
    sld.add_argument("--transition", type=float, default=0.5)
    sld.add_argument("--resolution", default="1920x1080")
    sld.add_argument("--fps", type=int, default=30)
    sld.add_argument("--music", default=None)

    # Video merger
    mrg = sub.add_parser("merge", help="Merge video clips")
    mrg.add_argument("--input", required=True, help="Videos folder or comma-separated paths")
    mrg.add_argument("--output", required=True)
    mrg.add_argument("--resolution", default="1920x1080")
    mrg.add_argument("--fps", type=int, default=30)

    args = parser.parse_args()

    if args.command == "duplicates":
        duplicate_finder.find_and_report(args.folder, args.threshold, args.delete, args.output)

    elif args.command == "enhance":
        p_input = Path(args.input)
        p_output = Path(args.output)
        if p_input.is_dir():
            photo_enhancer.enhance_folder(str(p_input), str(p_output), args.gamma, args.sharp, args.blur_threshold)
        else:
            p_output.parent.mkdir(parents=True, exist_ok=True)
            photo_enhancer.enhance_image(str(p_input), str(p_output), args.gamma, args.sharp, args.blur_threshold)

    elif args.command == "slideshow":
        paths = video_slideshow._list_images(args.input) if Path(args.input).is_dir() else args.input.split(',')
        video_slideshow.make_slideshow(paths, args.output, args.duration, args.transition,
                                       args.resolution, args.fps, args.music)
        print(f"Slideshow created: {args.output}")

    elif args.command == "merge":
        paths = video_merger._list_videos(args.input) if Path(args.input).is_dir() else args.input.split(',')
        video_merger.merge_videos(paths, args.output, args.resolution, args.fps)
        print(f"Merged video created: {args.output}")


if __name__ == "__main__":
    main()

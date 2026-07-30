import os
import json
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple, Dict

from PIL import Image
import imagehash


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS and path.is_file()


def _image_resolution(path: Path) -> int:
    try:
        with Image.open(path) as img:
            w, h = img.size
            return w * h
    except Exception:
        return 0


def compute_hashes(folder: str, hash_size: int = 16, quick: bool = False) -> Dict[str, imagehash.ImageHash]:
    """Compute perceptual hashes for every image in *folder*."""
    hashes: Dict[str, imagehash.ImageHash] = {}
    folder_path = Path(folder)
    for path in folder_path.iterdir():
        if not _is_image(path):
            continue
        try:
            with Image.open(path) as img:
                if quick:
                    h = imagehash.average_hash(img, hash_size=hash_size)
                else:
                    h = imagehash.phash(img, hash_size=hash_size)
            hashes[str(path)] = h
        except Exception as exc:
            print(f"[warn] cannot hash {path}: {exc}")
    return hashes


def group_duplicates(hashes: Dict[str, imagehash.ImageHash], threshold: int = 10) -> List[List[str]]:
    """Group image paths whose perceptual hashes are within *threshold* Hamming distance."""
    items = list(hashes.items())
    n = len(items)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        for j in range(i + 1, n):
            try:
                dist = items[i][1] - items[j][1]
            except TypeError:
                continue
            if dist <= threshold:
                union(i, j)

    groups: Dict[int, List[str]] = defaultdict(list)
    for i, (path, _) in enumerate(items):
        groups[find(i)].append(path)

    return [g for g in groups.values() if len(g) > 1]


def choose_best_keep(group: List[str]) -> str:
    """Return the path with the highest resolution (tie: first)."""
    return max(group, key=lambda p: _image_resolution(Path(p)))


def find_and_report(folder: str, threshold: int = 10, delete: bool = False, output: str = None) -> Dict:
    """Find duplicate groups, optionally remove lower-resolution copies, and return a report."""
    hashes = compute_hashes(folder)
    groups = group_duplicates(hashes, threshold)
    removed: List[str] = []
    kept: List[str] = []

    report_groups = []
    for group in groups:
        best = choose_best_keep(group)
        report_groups.append({
            "best": best,
            "duplicates": group,
            "best_resolution": _image_resolution(Path(best))
        })
        kept.append(best)
        if delete:
            for p in group:
                if p != best:
                    try:
                        os.remove(p)
                        removed.append(p)
                    except Exception as exc:
                        print(f"[warn] cannot delete {p}: {exc}")

    report = {
        "folder": folder,
        "threshold": threshold,
        "total_images": len(hashes),
        "duplicate_groups": len(groups),
        "groups": report_groups,
        "removed": removed,
        "kept": kept
    }

    if output:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {output}")

    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Find duplicate photos with perceptual hashing.")
    parser.add_argument("folder", help="Folder containing images")
    parser.add_argument("--threshold", type=int, default=10, help="Hamming distance threshold")
    parser.add_argument("--delete", action="store_true", help="Delete lower-resolution duplicates")
    parser.add_argument("--output", default="duplicates_report.json", help="JSON report path")
    parser.add_argument("--quick", action="store_true", help="Use average_hash instead of phash")
    args = parser.parse_args()

    find_and_report(args.folder, args.threshold, args.delete, args.output)
    print(f"Duplicate groups found: {len(group_duplicates(compute_hashes(args.folder, quick=args.quick), args.threshold))}")


if __name__ == "__main__":
    main()

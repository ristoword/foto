from pathlib import Path


BASE = Path("library")
ORIGINALS = BASE / "originals"
EDITED = BASE / "edited"
MUSIC = BASE / "music"
EXPORTS = BASE / "exports"

ORIGINAL_PHOTOS = ORIGINALS / "photos"
ORIGINAL_VIDEOS = ORIGINALS / "videos"
EDITED_PHOTOS = EDITED / "photos"
EDITED_VIDEOS = EDITED / "videos"

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}
MUSIC_EXTS = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'}


def init_library():
    for d in [ORIGINAL_PHOTOS, ORIGINAL_VIDEOS, EDITED_PHOTOS, EDITED_VIDEOS, MUSIC, EXPORTS]:
        d.mkdir(parents=True, exist_ok=True)


def list_originals(kind="photos"):
    d = ORIGINAL_PHOTOS if kind == "photos" else ORIGINAL_VIDEOS
    exts = IMAGE_EXTS if kind == "photos" else VIDEO_EXTS
    return sorted([str(f.resolve()) for f in d.iterdir() if f.suffix.lower() in exts and f.is_file()])


def list_edited(kind="photos"):
    d = EDITED_PHOTOS if kind == "photos" else EDITED_VIDEOS
    exts = IMAGE_EXTS if kind == "photos" else VIDEO_EXTS
    return sorted([str(f.resolve()) for f in d.iterdir() if f.suffix.lower() in exts and f.is_file()])


def list_music():
    return sorted([str(f.resolve()) for f in MUSIC.iterdir() if f.suffix.lower() in MUSIC_EXTS and f.is_file()])


def save_to(kind, uploaded_file, area="originals"):
    base = (ORIGINAL_PHOTOS if kind == "photos" else
            ORIGINAL_VIDEOS if kind == "videos" else
            MUSIC if kind == "music" else
            BASE / area / kind)
    base.mkdir(parents=True, exist_ok=True)
    fpath = (base / uploaded_file.name).resolve()
    with open(fpath, "wb") as f:
        f.write(uploaded_file.getvalue())
    return str(fpath)


def save_to_edited(uploaded_file, kind="photos"):
    return save_to(kind, uploaded_file, area="edited")


def next_version(path):
    p = Path(path)
    if not p.exists():
        return str(p.resolve())
    stem = p.stem
    suffix = p.suffix
    # if stem already ends with _vN, increment
    if "_v" in stem:
        base, _, num = stem.rpartition("_v")
        try:
            n = int(num)
        except ValueError:
            base = stem
            n = 0
    else:
        base = stem
        n = 0
    parent = p.parent
    i = n + 1
    while True:
        candidate = parent / f"{base}_v{i}{suffix}"
        if not candidate.exists():
            return str(candidate.resolve())
        i += 1

"""Project management: each project gets its own media folder."""
import json
import shutil
import time
from pathlib import Path

import library

PROJECTS_BASE = library.BASE / "projects"


def init_projects():
    PROJECTS_BASE.mkdir(parents=True, exist_ok=True)


def _safe_name(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")


def list_projects():
    init_projects()
    projects = []
    for d in sorted(PROJECTS_BASE.iterdir()):
        if d.is_dir():
            meta_file = d / "meta.json"
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text())
                except Exception:
                    meta = {"name": d.name, "created": 0, "description": ""}
            else:
                meta = {"name": d.name, "created": 0, "description": ""}
            meta["folder"] = d.name
            projects.append(meta)
    return sorted(projects, key=lambda x: x.get("created", 0), reverse=True)


def create_project(name: str, description: str = "") -> str:
    init_projects()
    folder = _safe_name(name)
    if not folder:
        raise ValueError("Nome progetto non valido")
    p = PROJECTS_BASE / folder
    (p / "photos").mkdir(parents=True, exist_ok=True)
    (p / "videos").mkdir(parents=True, exist_ok=True)
    (p / "exports").mkdir(parents=True, exist_ok=True)
    (p / "music").mkdir(parents=True, exist_ok=True)
    meta = {"name": name, "folder": folder, "description": description, "created": time.time()}
    (p / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return str(p)


def get_project_path(folder: str) -> Path:
    return PROJECTS_BASE / folder


def get_project_photos(folder: str):
    d = PROJECTS_BASE / folder / "photos"
    if not d.exists():
        return []
    return sorted([str(f.resolve()) for f in d.iterdir() if f.suffix.lower() in library.IMAGE_EXTS and f.is_file()])


def get_project_videos(folder: str):
    d = PROJECTS_BASE / folder / "videos"
    if not d.exists():
        return []
    return sorted([str(f.resolve()) for f in d.iterdir() if f.suffix.lower() in library.VIDEO_EXTS and f.is_file()])


def get_project_music(folder: str):
    d = PROJECTS_BASE / folder / "music"
    if not d.exists():
        return []
    return sorted([str(f.resolve()) for f in d.iterdir() if f.suffix.lower() in library.MUSIC_EXTS and f.is_file()])


def get_project_exports(folder: str):
    d = PROJECTS_BASE / folder / "exports"
    if not d.exists():
        return []
    exts = library.IMAGE_EXTS | library.VIDEO_EXTS
    return sorted([str(f.resolve()) for f in d.iterdir() if f.suffix.lower() in exts and f.is_file()])


def save_to_project(folder: str, uploaded_file, kind: str = "photos") -> str:
    d = PROJECTS_BASE / folder / kind
    d.mkdir(parents=True, exist_ok=True)
    fpath = d / uploaded_file.name
    with open(fpath, "wb") as f:
        f.write(uploaded_file.getvalue())
    return str(fpath.resolve())


def copy_to_project(folder: str, src_path: str, kind: str = "photos") -> str:
    d = PROJECTS_BASE / folder / kind
    d.mkdir(parents=True, exist_ok=True)
    src = Path(src_path)
    dst = d / src.name
    shutil.copy2(src, dst)
    return str(dst.resolve())


def delete_file(file_path: str) -> bool:
    p = Path(file_path)
    if p.is_file():
        p.unlink()
        return True
    return False


def delete_project(folder: str) -> bool:
    p = PROJECTS_BASE / folder
    if p.exists():
        shutil.rmtree(p)
        return True
    return False


def get_project_stats(folder: str) -> dict:
    p = PROJECTS_BASE / folder
    photos = get_project_photos(folder)
    videos = get_project_videos(folder)
    exports = get_project_exports(folder)
    total_size = sum(Path(f).stat().st_size for f in photos + videos + exports if Path(f).exists())
    return {
        "photos": len(photos),
        "videos": len(videos),
        "exports": len(exports),
        "size_mb": round(total_size / (1024 * 1024), 2),
    }

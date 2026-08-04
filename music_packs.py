"""
Pacchetti musica preinstallati stile iMovie / Canva / CapCut.

NOTA LEGALE: non possiamo includere la musica proprietaria di Apple/Canva/ByteDance.
Usiamo tracce royalty-free (SoundHelix) organizzate negli stessi stili d'uso tipici
di quei programmi (cinematico, social, reels/energetico).
"""
from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import library

PACK_ROOT = library.MUSIC

# Tracce SoundHelix (royalty-free examples) mappate per stile
PACKS: Dict[str, List[Tuple[str, str, str]]] = {
    # (filename, url, descrizione)
    "imovie": [
        (
            "iMovie_Cinema_Emotivo.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            "Cinematico emotivo — ideale per ricordi e film familiari",
        ),
        (
            "iMovie_Memorie.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
            "Soft e nostalgico — slideshow di foto",
        ),
        (
            "iMovie_Tramonto.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
            "Atmosfera calda — viaggi e tramonti",
        ),
        (
            "iMovie_Viaggio.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-15.mp3",
            "Avventura leggera — road trip e vacanze",
        ),
    ],
    "canva": [
        (
            "Canva_Social_Bright.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
            "Bright e positivo — post Instagram / Canva",
        ),
        (
            "Canva_Corporate_Clean.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
            "Pulito e professionale — presentazioni",
        ),
        (
            "Canva_Lifestyle.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
            "Lifestyle moderno — brand e storytelling",
        ),
        (
            "Canva_Happy_Days.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3",
            "Upbeat felice — promo e social ads",
        ),
    ],
    "capcut": [
        (
            "CapCut_Reels_Energy.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
            "Energia alta — Reels e TikTok",
        ),
        (
            "CapCut_Beat_Drop.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
            "Beat moderno — trend e transizioni rapide",
        ),
        (
            "CapCut_Viral_Pulse.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3",
            "Pulse ritmato — montaggi dinamici",
        ),
        (
            "CapCut_Night_Drive.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3",
            "Night vibe — aesthetic e vlog",
        ),
    ],
}

PACK_LABELS = {
    "imovie": "🎬 iMovie",
    "canva": "🎨 Canva",
    "capcut": "✂️ CapCut",
}


def pack_dir(pack: str) -> Path:
    d = PACK_ROOT / pack
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_pack_tracks(pack: Optional[str] = None) -> List[str]:
    """Elenca tracce preinstallate (una cartella o tutte)."""
    packs = [pack] if pack else list(PACKS.keys())
    out: List[str] = []
    for p in packs:
        d = pack_dir(p)
        for f in sorted(d.iterdir()):
            if f.suffix.lower() in library.MUSIC_EXTS and f.is_file():
                out.append(str(f.resolve()))
    return out


def list_music_grouped() -> Dict[str, List[str]]:
    """Restituisce {pack_label: [paths]} + eventuale musica utente."""
    grouped: Dict[str, List[str]] = {}
    for pack, label in PACK_LABELS.items():
        tracks = list_pack_tracks(pack)
        if tracks:
            grouped[label] = tracks
    # Musica caricata dall'utente (root music/, non nelle sottocartelle pack)
    user = []
    if library.MUSIC.is_dir():
        for f in sorted(library.MUSIC.iterdir()):
            if f.is_file() and f.suffix.lower() in library.MUSIC_EXTS:
                user.append(str(f.resolve()))
    if user:
        grouped["📁 Le tue musiche"] = user
    return grouped


def is_pack_ready(pack: str) -> bool:
    expected = {name for name, _, _ in PACKS.get(pack, [])}
    if not expected:
        return False
    existing = {f.name for f in pack_dir(pack).iterdir() if f.is_file()}
    return expected.issubset(existing)


def all_packs_ready() -> bool:
    return all(is_pack_ready(p) for p in PACKS)


def _download(url: str, dest: Path, timeout: int = 120) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AppFotoStudio/1.0 (royalty-free music setup)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(tmp, "wb") as out:
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            out.write(chunk)
    tmp.replace(dest)


def ensure_music_packs(force: bool = False, progress=None) -> Dict[str, int]:
    """
    Scarica i pacchetti mancanti.
    progress: callback opzionale (msg: str) -> None
    """
    library.init_library()
    stats = {"downloaded": 0, "skipped": 0, "failed": 0}

    def log(msg: str):
        if progress:
            progress(msg)
        else:
            print(msg)

    for pack, tracks in PACKS.items():
        d = pack_dir(pack)
        log(f"Pacchetto {PACK_LABELS.get(pack, pack)}…")
        for name, url, desc in tracks:
            dest = d / name
            if dest.is_file() and not force and dest.stat().st_size > 100_000:
                stats["skipped"] += 1
                continue
            try:
                log(f"  ↓ {name} — {desc}")
                _download(url, dest)
                if dest.stat().st_size < 50_000:
                    dest.unlink(missing_ok=True)
                    raise RuntimeError("file troppo piccolo, download incompleto")
                stats["downloaded"] += 1
            except Exception as e:
                stats["failed"] += 1
                log(f"  ✗ Errore {name}: {e}")
                dest.unlink(missing_ok=True)
    return stats


def flat_options_with_labels() -> List[Tuple[str, str]]:
    """Lista (path, label_visualizzata) per selectbox Streamlit."""
    options: List[Tuple[str, str]] = []
    for pack, label in PACK_LABELS.items():
        for path in list_pack_tracks(pack):
            options.append((path, f"{label} · {Path(path).stem.replace('_', ' ')}"))
    for path in list_music_grouped().get("📁 Le tue musiche", []):
        options.append((path, f"📁 {Path(path).name}"))
    return options


if __name__ == "__main__":
    print("Installazione pacchetti musica iMovie / Canva / CapCut…")
    result = ensure_music_packs()
    print(result)
    print("Tracce disponibili:")
    for label, tracks in list_music_grouped().items():
        print(f"  {label}: {len(tracks)}")
        for t in tracks:
            print(f"    - {Path(t).name}")

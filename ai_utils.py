"""
ai_utils.py — OpenAI integration for AppFoto Studio.

Configuration is read from environment variables (via .env):
  OPENAI_API_KEY      — required
  OPENAI_MODEL        — default "gpt-4o"
  OPENAI_MAX_TOKENS   — default "1024"
  OPENAI_TEMPERATURE  — default "0.7"

All public functions return strings or dicts and never raise; errors are
returned as Italian error strings starting with "⚠️".
"""
import os
import json
import base64
from pathlib import Path

from openai import OpenAI


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _client() -> OpenAI:
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))


def _model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o")


def _max_tokens() -> int:
    try:
        return int(os.environ.get("OPENAI_MAX_TOKENS", "1024"))
    except ValueError:
        return 1024


def _temperature() -> float:
    try:
        return float(os.environ.get("OPENAI_TEMPERATURE", "0.7"))
    except ValueError:
        return 0.7


def _encode_image(image_path: str):
    """Return (base64_data, mime_type) for an image file."""
    ext = Path(image_path).suffix.lower().lstrip(".")
    mime_map = {
        "jpg": "jpeg", "jpeg": "jpeg", "png": "png",
        "webp": "webp", "gif": "gif", "bmp": "jpeg",
        "tiff": "jpeg", "tif": "jpeg",
    }
    mime = f"image/{mime_map.get(ext, 'jpeg')}"
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8"), mime


def _parse_json(raw: str) -> dict:
    """Parse JSON from a possibly markdown-fenced AI response."""
    s = raw.strip()
    for prefix in ("```json", "```"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    if s.endswith("```"):
        s = s[:-3]
    return json.loads(s.strip())


_SYSTEM_IT = (
    "Sei un assistente esperto di fotografia e video editing integrato in AppFoto Studio. "
    "Rispondi sempre in italiano, in modo conciso e professionale."
)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def ask(prompt: str, system: str = _SYSTEM_IT) -> str:
    """Generic text completion; returns Italian prose."""
    try:
        resp = _client().chat.completions.create(
            model=_model(),
            max_tokens=_max_tokens(),
            temperature=_temperature(),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        return f"⚠️ Errore AI: {exc}"


def describe_image(
    image_path: str,
    question: str = (
        "Descrivi questa immagine in dettaglio: soggetto, colori, "
        "composizione e qualità tecnica."
    ),
) -> str:
    """Describe an image with GPT-4o vision."""
    try:
        b64, mime = _encode_image(image_path)
        resp = _client().chat.completions.create(
            model=_model(),
            max_tokens=_max_tokens(),
            temperature=_temperature(),
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                    {"type": "text", "text": question},
                ],
            }],
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        return f"⚠️ Errore AI: {exc}"


# ---------------------------------------------------------------------------
# Tab-specific AI features
# ---------------------------------------------------------------------------

def suggest_enhance_params(image_path: str) -> dict:
    """
    Analyze a photo and suggest enhancement parameters.
    Returns: {"gamma": float, "sharpness": float, "reason": str}
    """
    q = (
        "Analizza questa immagine e suggerisci i migliori parametri per il miglioramento automatico.\n"
        "Rispondi SOLO con JSON valido (senza blocchi markdown) nel formato esatto:\n"
        '{"gamma": <float 0.7-2.0>, "sharpness": <float 0.0-3.0>, "reason": "<spiegazione breve>"}\n'
        "Nota: gamma > 1 schiarisce; sharpness alta aumenta la nitidezza."
    )
    raw = describe_image(image_path, q)
    try:
        d = _parse_json(raw)
        return {
            "gamma": round(max(0.5, min(2.5, float(d["gamma"]))), 2),
            "sharpness": round(max(0.0, min(3.0, float(d["sharpness"]))), 2),
            "reason": str(d.get("reason", "")),
        }
    except Exception:
        return {"gamma": 1.2, "sharpness": 1.0, "reason": raw}


def suggest_edit_settings(image_path: str) -> dict:
    """
    Analyze a photo and suggest photo editor settings.
    Returns: {"brightness": float, "contrast": float, "saturation": float,
              "sharpen": float, "filter": str, "reason": str}
    """
    q = (
        "Analizza questa immagine e suggerisci le impostazioni ottimali per l'editor fotografico.\n"
        "Rispondi SOLO con JSON valido (senza markdown):\n"
        '{"brightness": <0.5-2.0>, "contrast": <0.5-2.0>, "saturation": <0.5-2.0>, '
        '"sharpen": <0.0-2.0>, '
        '"filter": "<nessuno|grayscale|sepia|blur|sharpen|emboss|edge|contour>", '
        '"reason": "<motivazione breve>"}'
    )
    raw = describe_image(image_path, q)
    try:
        d = _parse_json(raw)
        f = str(d.get("filter", "nessuno"))
        if f not in {"nessuno", "grayscale", "sepia", "blur", "sharpen", "emboss", "edge", "contour"}:
            f = "nessuno"
        return {
            "brightness": round(max(0.1, min(3.0, float(d.get("brightness", 1.0)))), 2),
            "contrast":   round(max(0.1, min(3.0, float(d.get("contrast",   1.0)))), 2),
            "saturation": round(max(0.0, min(3.0, float(d.get("saturation", 1.0)))), 2),
            "sharpen":    round(max(0.0, min(2.0, float(d.get("sharpen",    0.0)))), 2),
            "filter":     f,
            "reason":     str(d.get("reason", "")),
        }
    except Exception:
        return {
            "brightness": 1.0, "contrast": 1.0, "saturation": 1.0,
            "sharpen": 0.0, "filter": "nessuno", "reason": raw,
        }


def analyze_duplicate_group(group: dict) -> str:
    """Recommend which duplicate to keep and why."""
    best_name = Path(group["best"]).name
    dup_names = [Path(p).name for p in group["duplicates"]]
    prompt = (
        f"Gruppo di foto duplicate trovato:\n"
        f"  Foto migliore (risoluzione più alta): {best_name} ({group['best_resolution']} pixel totali)\n"
        f"  Tutte le copie: {', '.join(dup_names)}\n\n"
        "Spiega in 2-3 righe perché mantenere la copia ad alta risoluzione e cosa fare con le altre."
    )
    return ask(prompt)


def generate_slideshow_metadata(n_photos: int, folder_name: str = "", photo_names=None) -> dict:
    """
    Generate a creative title, description and optimal duration for a slideshow.
    Returns: {"title": str, "description": str, "duration": float}
    """
    names_str = ""
    if photo_names:
        names_str = f"\nFile presenti: {', '.join(list(photo_names)[:8])}"
    prompt = (
        f"Stai creando uno slideshow con {n_photos} foto.{names_str}\n"
        f"Cartella sorgente: '{folder_name}'\n\n"
        "Genera metadati creativi per questo slideshow. "
        "Rispondi SOLO con JSON valido (senza markdown):\n"
        '{"title": "<titolo creativo>", "description": "<1-2 frasi>", "duration": <float 2.0-6.0>}'
    )
    raw = ask(prompt)
    try:
        d = _parse_json(raw)
        return {
            "title":       str(d.get("title", "Il mio slideshow")),
            "description": str(d.get("description", "")),
            "duration":    round(max(2.0, min(8.0, float(d.get("duration", 3.0)))), 1),
        }
    except Exception:
        return {"title": "Il mio slideshow", "description": raw, "duration": 3.0}


def suggest_merge_order(video_names: list) -> str:
    """Suggest narrative order and structure for video clips to merge."""
    if not video_names:
        return "Nessun video disponibile da analizzare."
    prompt = (
        "Hai questi clip video da unire (nell'ordine attuale):\n"
        + "\n".join(f"  {i+1}. {n}" for i, n in enumerate(video_names))
        + "\n\nSuggerisci l'ordine narrativo ottimale e come strutturare il montaggio. "
        "Sii conciso (max 4 righe)."
    )
    return ask(prompt)


def suggest_video_filter(video_name: str) -> str:
    """Recommend the best filter for a video based on its filename."""
    prompt = (
        f"Video: '{video_name}'\n"
        "Filtri disponibili: grayscale, blur, negate, edgedetect, vignette, sharpen\n"
        "Quale filtro consigli per questo video e perché? (max 2 righe)"
    )
    return ask(prompt)


def suggest_trim_points(video_name: str) -> str:
    """Suggest a trim strategy for a video clip."""
    prompt = (
        f"Video: '{video_name}'\n"
        "Sei un editor professionista. Fornisci consigli generali sulla strategia di taglio ideale "
        "(intro, corpo, chiusura). Sii concreto e breve (max 3 righe)."
    )
    return ask(prompt)


def suggest_audio_pairing(video_name: str, music_names: list) -> str:
    """Suggest the best music track to pair with a video."""
    if not music_names:
        return "Nessuna traccia musicale disponibile nella libreria."
    prompt = (
        f"Video: '{video_name}'\n"
        f"Tracce musicali disponibili: {', '.join(music_names)}\n\n"
        "Quale traccia abbineresti a questo video e perché? (max 2 righe)"
    )
    return ask(prompt)


def suggest_frame_interval(video_name: str) -> str:
    """Suggest an optimal frame extraction interval."""
    prompt = (
        f"Video: '{video_name}'\n"
        "Quale intervallo in secondi consigli per estrarre frame significativi da questo video? "
        "Indica il numero e la motivazione in 1-2 righe."
    )
    return ask(prompt)


def check_face_swap_quality(image_path: str) -> str:
    """Analyze a photo's suitability for face swap."""
    return describe_image(
        image_path,
        "Questa immagine è adatta per un face swap? Valuta: qualità e leggibilità del volto, "
        "illuminazione, angolazione, risoluzione. Dai un punteggio da 1 a 10 e 2-3 consigli pratici."
    )


def summarize_activity(jobs: list, is_admin: bool = False) -> str:
    """Natural language summary of job history."""
    if not jobs:
        return "Nessuna attività registrata al momento."
    lines = []
    for j in jobs[:20]:
        if is_admin and len(j) >= 7:
            lines.append(f"tipo={j[2]}, stato={j[5]}, data={j[6]}")
        elif len(j) >= 6:
            lines.append(f"tipo={j[1]}, stato={j[4]}, data={j[5]}")
    prompt = (
        "Analizza questo storico operazioni AppFoto Studio e scrivi un riepilogo in linguaggio naturale "
        "(max 5 righe). Indica operazioni frequenti, eventuali errori e un consiglio per ottimizzare il flusso.\n\n"
        + "\n".join(lines)
    )
    return ask(prompt)


def analyze_admin_activity(users: list, total_jobs: int) -> str:
    """Generate admin insights about platform usage."""
    n_admin = sum(1 for u in users if len(u) > 2 and u[2])
    prompt = (
        f"Report amministratore AppFoto Studio:\n"
        f"  Utenti totali: {len(users)} (di cui {n_admin} admin)\n"
        f"  Lavori totali registrati: {total_jobs}\n\n"
        "Fornisci un report breve sulla salute della piattaforma e 2-3 suggerimenti gestionali (max 4 righe)."
    )
    return ask(prompt)


def analyze_library(
    n_photos: int,
    n_videos: int,
    n_music: int,
    n_edited_photos: int,
    n_edited_videos: int,
    size_mb: float,
) -> str:
    """Generate insights and tips about the media library."""
    prompt = (
        f"Libreria AppFoto Studio:\n"
        f"  Foto originali: {n_photos}  |  Video originali: {n_videos}  |  Musica: {n_music}\n"
        f"  Foto modificate: {n_edited_photos}  |  Video prodotti: {n_edited_videos}\n"
        f"  Spazio totale: {size_mb:.1f} MB\n\n"
        "Fornisci un'analisi della libreria e 3 suggerimenti pratici per organizzarla o ottimizzarla (max 5 righe)."
    )
    return ask(prompt)


def suggest_music_mood(filename: str) -> str:
    """Suggest mood/genre tags for a music file based on its filename."""
    prompt = (
        f"File audio: '{filename}'\n"
        "Basandoti solo sul nome del file, suggerisci: mood (es. romantico, energico, malinconico), "
        "genere probabile e un caso d'uso ideale in AppFoto (es. 'perfetto per slideshow di viaggi'). "
        "Formato: 1-2 righe."
    )
    return ask(prompt)


def caption_photo(image_path: str) -> str:
    """Generate a short professional caption for a saved photo."""
    return describe_image(
        image_path,
        "Scrivi una didascalia professionale e coinvolgente per questa foto. Massimo 1-2 righe."
    )


def suggest_photopea_edits(image_path: str) -> str:
    """Suggest specific Photopea edit steps for a photo."""
    return describe_image(
        image_path,
        "Sei un esperto di Photopea (editor grafico web). Analizza questa foto e fornisci "
        "5 passaggi numerati e specifici per migliorarla in Photopea "
        "(usa strumenti reali: Livelli, Curve, Clone Stamp, Healing Brush, ecc.)."
    )


def chat(messages: list) -> str:
    """
    AppFoto AI assistant: general-purpose Italian chat.
    messages is a list of {"role": "user"|"assistant", "content": str} dicts.
    """
    system = (
        "Sei l'assistente AI integrato di AppFoto Studio, un'app professionale per "
        "la gestione e modifica di foto e video.\n"
        "Funzionalità: rilevamento duplicati, miglioramento automatico foto, slideshow, "
        "unione video, editor video avanzato, editor foto (curve, HSL, vignettatura, duotono), "
        "face swap, libreria media, storico lavori.\n"
        "Aiuta l'utente con domande su fotografia, video editing, colore, composizione e uso dell'app. "
        "Rispondi sempre in italiano, in modo conciso e professionale."
    )
    try:
        resp = _client().chat.completions.create(
            model=_model(),
            max_tokens=_max_tokens(),
            temperature=_temperature(),
            messages=[{"role": "system", "content": system}] + messages,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        return f"⚠️ Errore AI: {exc}"

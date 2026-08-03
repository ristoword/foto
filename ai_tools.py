"""Strumenti AI con OpenAI API - Generazione immagini, analisi, suggerimenti."""
import os
import base64
import tempfile
import requests as req
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False


def is_configured():
    return OPENAI_AVAILABLE and bool(os.environ.get("OPENAI_API_KEY", ""))


def _get_client():
    if not OPENAI_AVAILABLE:
        raise ImportError("Libreria openai non installata. Esegui: pip install openai")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or api_key == "sk-...":
        raise ValueError(
            "OPENAI_API_KEY non configurata. Inserisci la tua chiave nel file .env"
        )
    return openai.OpenAI(api_key=api_key)


def _model():
    return os.environ.get("OPENAI_MODEL", "gpt-4o")


def _max_tokens():
    return int(os.environ.get("OPENAI_MAX_TOKENS", "1024"))


def _temperature():
    return float(os.environ.get("OPENAI_TEMPERATURE", "0.7"))


def generate_image(prompt, size="1024x1024", quality="hd", style="natural", n=1):
    """Genera immagini con DALL-E 3."""
    client = _get_client()
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality=quality,
        style=style,
        n=n,
    )
    return [img.url for img in response.data]


def download_image(url, save_path):
    """Scarica un'immagine da URL e la salva localmente."""
    r = req.get(url, timeout=60)
    r.raise_for_status()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(r.content)
    return save_path


def create_variation(image_path, n=1, size="1024x1024"):
    """Crea variazioni di un'immagine con DALL-E 2."""
    client = _get_client()
    with open(image_path, "rb") as img_file:
        response = client.images.create_variation(
            model="dall-e-2",
            image=img_file,
            n=n,
            size=size,
        )
    return [img.url for img in response.data]


def analyze_image(image_path, prompt="Descrivi questa immagine in dettaglio in italiano."):
    """Analizza un'immagine con GPT-4o Vision."""
    client = _get_client()
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    ext = Path(image_path).suffix.lower().lstrip(".")
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "webp": "image/webp", "gif": "image/gif", "bmp": "image/bmp",
    }
    mime = mime_map.get(ext, "image/jpeg")
    response = client.chat.completions.create(
        model=_model(),
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ],
            }
        ],
        max_tokens=_max_tokens(),
        temperature=_temperature(),
    )
    return response.choices[0].message.content


def suggest_edits(image_path):
    """Suggerisce miglioramenti professionali per una foto."""
    prompt = (
        "Sei un fotografo professionista e ritoccatore esperto. "
        "Analizza questa immagine e suggerisci miglioramenti specifici. Includi: "
        "1) Esposizione e luminosità  2) Contrasto e toni  3) Saturazione e colori  "
        "4) Bilanciamento del bianco  5) Nitidezza e dettagli  6) Composizione  "
        "7) Suggerimenti per il ritocco  8) Valutazione complessiva (voto da 1 a 10). "
        "Rispondi in italiano con formato lista puntata."
    )
    return analyze_image(image_path, prompt)


def generate_caption(image_path, style="social"):
    """Genera didascalie per social media o uso professionale."""
    styles = {
        "social": (
            "Genera una didascalia accattivante per Instagram/social media "
            "per questa foto. Includi 5-8 hashtag pertinenti. Scrivi in italiano."
        ),
        "professionale": (
            "Genera una descrizione professionale e formale per questa foto, "
            "adatta a un portfolio o sito web. Scrivi in italiano."
        ),
        "poetica": (
            "Scrivi una breve poesia o frase poetica ispirata da questa foto. "
            "Scrivi in italiano."
        ),
        "giornalistica": (
            "Scrivi una didascalia in stile giornalistico per questa foto, "
            "come per un articolo di giornale. Scrivi in italiano."
        ),
        "e-commerce": (
            "Scrivi una descrizione di prodotto persuasiva per e-commerce "
            "basata su questa foto. Scrivi in italiano."
        ),
    }
    prompt = styles.get(style, styles["social"])
    return analyze_image(image_path, prompt)


def ai_chat(message, context=None):
    """Chat con assistente AI esperto di fotografia e video."""
    if context is None:
        context = (
            "Sei un assistente esperto di fotografia professionale, "
            "ritocco fotografico, montaggio video e post-produzione. "
            "Conosci tutti i software professionali (Photoshop, Lightroom, "
            "Premiere Pro, DaVinci Resolve, After Effects). "
            "Rispondi sempre in italiano in modo chiaro e pratico."
        )
    client = _get_client()
    response = client.chat.completions.create(
        model=_model(),
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": message},
        ],
        max_tokens=_max_tokens(),
        temperature=_temperature(),
    )
    return response.choices[0].message.content


def batch_analyze(image_paths, prompt=None):
    """Analizza più immagini e restituisce un report comparativo."""
    if prompt is None:
        prompt = (
            "Analizza queste immagini e fornisci un report comparativo. "
            "Per ogni immagine indica punti di forza e debolezza. "
            "Suggerisci quale è la migliore e perché. Rispondi in italiano."
        )
    results = []
    for path in image_paths:
        try:
            analysis = analyze_image(path, "Descrivi brevemente questa foto in 2 frasi in italiano.")
            results.append({"path": path, "analysis": analysis})
        except Exception as e:
            results.append({"path": path, "analysis": f"Errore: {e}"})
    return results

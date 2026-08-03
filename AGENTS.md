# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
AppFoto Studio: a Python photo/video toolkit. Two entrypoints share the same modules:
- `dashboard.py` — the primary product, a Streamlit web UI (Italian) for duplicate detection, photo enhancement, slideshows, video merge/edit, face swap, etc.
- `main.py` — a CLI exposing a subset (`duplicates`, `enhance`, `slideshow`, `merge`).

Media handling lives in `library.py`, which creates a local `library/` directory (originals/edited/music/exports) on startup. `db.py`/`auth.py` provide optional Postgres-backed auth, uploads, and job history.

### Running (dev)
The update script provisions a `.venv` with dependencies. Run the web app with:
`.venv/bin/streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true`
Streamlit reruns the whole script on every widget interaction, so waits between UI actions are expected.

### Auth / environment (important, non-obvious)
- A `.env` (loaded via python-dotenv) drives auth. There are two mutually exclusive modes:
  - If `DATABASE_URL` is set AND `psycopg2` imports, auth is Postgres-backed and history/admin/upload-logging tabs are live.
  - Otherwise the app falls back to a single env user (`APP_USERNAME` / `APP_PASSWORD`); DB-backed features (Storico/Admin/Lavori) render but stay empty.
- `.env.example` points `DATABASE_URL` at an external Railway *production* Postgres. Do NOT use that for local dev. For a self-contained dev setup, create a `.env` with only `APP_USERNAME`/`APP_PASSWORD` (no `DATABASE_URL`) and log in with those.

### System deps
`ffmpeg` is required for slideshow/merge/video-editor features (already present in the environment). OpenCV is the `-headless` build, so no display libs are needed.

### AI (OpenAI)
L'app integra OpenAI GPT-4o tramite `ai_utils.py`. Le variabili necessarie in `.env` sono:
```
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=1024
OPENAI_TEMPERATURE=0.7
```
Senza `OPENAI_API_KEY` le funzioni AI restituiscono messaggi `⚠️ Errore AI: ...` ma non sollevano eccezioni. Le chiamate vision (analisi immagini) usano GPT-4o multimodale via base64 encoding.

### Lint / tests
There is no lint config and no automated test suite in this repo. The only static check available is byte-compilation, e.g. `.venv/bin/python -m py_compile *.py`.

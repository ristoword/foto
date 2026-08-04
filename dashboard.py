import os
import numpy as np
import streamlit as st
from pathlib import Path

import duplicate_finder
import photo_enhancer
import photo_editor
import face_swap
import video_slideshow
import video_merger
import video_editor
import auth
import db
import library
import ai_tools

library.init_library()


def _log(job_type, input_summary, output_path, status="ok"):
    user_id = auth.current_user_id()
    if user_id:
        db.log_job(user_id, job_type, input_summary, output_path, status)


st.set_page_config(page_title="AppFoto Studio Pro", layout="wide", page_icon="🎬")
auth.require_login()

# ── CSS PROFESSIONALE ────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root {
        --accent: #00f2ff;
        --accent-dark: #00b8c4;
        --accent-glow: rgba(0, 242, 255, 0.3);
        --gold: #f2c94c;
        --bg: #09090b;
        --surface: #111113;
        --surface-2: #18181b;
        --surface-3: #1f1f23;
        --border: #27272a;
        --text: #f4f4f5;
        --muted: #a1a1aa;
        --success: #22c55e;
        --danger: #ef4444;
    }
    .stApp {
        background: linear-gradient(135deg, var(--bg) 0%, #0c0c14 100%);
        color: var(--text);
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }
    h1, h2, h3 { color: var(--accent); font-weight: 700; }
    .main-header {
        text-align: center;
        padding: 0.5rem 0 0.2rem 0;
        background: linear-gradient(180deg, rgba(0,242,255,0.06) 0%, transparent 100%);
        border-bottom: 1px solid var(--border);
        margin-bottom: 0.5rem;
    }
    .main-header h1 {
        font-size: 3rem; font-weight: 900; letter-spacing: -2px;
        text-transform: uppercase;
        background: linear-gradient(135deg, var(--accent) 0%, var(--gold) 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: none;
    }
    .sub-header {
        text-align: center; color: var(--muted); font-size: 0.85rem;
        font-weight: 500; letter-spacing: 0.4em; text-transform: uppercase;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px; background: var(--surface); padding: 0.5rem 0.8rem 0;
        border-radius: 12px 12px 0 0; border-bottom: 2px solid var(--border);
        overflow-x: auto;
    }
    .stTabs [data-baseweb="tab"] {
        background: var(--surface-2); color: var(--muted);
        border-radius: 8px 8px 0 0; padding: 10px 16px;
        font-weight: 600; font-size: 0.82rem;
        border: 1px solid var(--border); border-bottom: none;
        white-space: nowrap;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent), var(--accent-dark));
        color: #0a0a0a; border-color: var(--accent);
        box-shadow: 0 -3px 12px var(--accent-glow);
    }
    div.stButton > button:first-child {
        background: linear-gradient(135deg, var(--accent), var(--accent-dark));
        color: #0a0a0a; border: none; border-radius: 8px;
        padding: 0.6rem 1.4rem; font-weight: 700;
        box-shadow: 0 4px 14px var(--accent-glow);
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        box-shadow: 0 6px 20px var(--accent-glow);
        transform: translateY(-1px);
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stSlider"] label,
    div[data-testid="stSelectbox"] label { color: var(--text) !important; font-weight: 500; }
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stSelectbox"] > div > div {
        background: var(--surface-2) !important; color: var(--text) !important;
        border: 1px solid var(--border) !important; border-radius: 6px !important;
    }
    .stSidebar { background: var(--surface) !important; border-right: 1px solid var(--border); }
    .stSidebar [data-testid="stMetric"] {
        background: var(--surface-2); border: 1px solid var(--border);
        border-radius: 8px; padding: 0.4rem;
    }
    .stInfo { background: var(--surface-2); border-left: 4px solid var(--accent); }
    .stSuccess { background: #0f2f1a; border-left: 4px solid var(--success); }
    .stError { background: #2f1010; border-left: 4px solid var(--danger); }
    .pro-card {
        background: var(--surface-2); border: 1px solid var(--border);
        border-radius: 12px; padding: 1.2rem; margin: 0.5rem 0;
        transition: all 0.2s;
    }
    .pro-card:hover { border-color: var(--accent); box-shadow: 0 4px 16px var(--accent-glow); }
    .stat-card {
        background: linear-gradient(135deg, var(--surface-2), var(--surface-3));
        border: 1px solid var(--border); border-radius: 10px;
        padding: 1rem; text-align: center;
    }
    .stat-card h3 { font-size: 2rem; margin: 0; }
    .stat-card p { color: var(--muted); font-size: 0.8rem; margin: 0; }
    .tool-badge {
        display: inline-block; background: var(--accent);
        color: #0a0a0a; padding: 2px 10px; border-radius: 12px;
        font-size: 0.72rem; font-weight: 700; margin: 2px;
    }
    .ai-badge {
        display: inline-block; background: linear-gradient(135deg, #a855f7, #ec4899);
        color: white; padding: 2px 10px; border-radius: 12px;
        font-size: 0.72rem; font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🎬 AppFoto Studio Pro</h1></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Suite professionale di editing foto e video · AI integrata</div>',
    unsafe_allow_html=True,
)

IMAGE_EXTS = library.IMAGE_EXTS
VIDEO_EXTS = library.VIDEO_EXTS
MUSIC_EXTS = library.MUSIC_EXTS


# ── FUNZIONI HELPER ──────────────────────────────────────────────────────────
def _save_upload(uploaded_file, kind="photos"):
    if uploaded_file is None:
        return None
    return library.save_to(kind, uploaded_file)


def _save_uploads(uploaded_files, kind="photos"):
    if not uploaded_files:
        return []
    return [library.save_to(kind, up) for up in uploaded_files]


def _refresh_library():
    imgs = library.list_originals("photos")
    vids = library.list_originals("videos")
    music = library.list_music()
    st.session_state.library_images = imgs
    st.session_state.library_videos = vids
    st.session_state.library_music = music
    return imgs, vids, music


def _image_picker(label, key, library_key):
    lib = st.session_state.get(library_key, [])
    if not lib:
        st.info("Nessun file nella libreria. Carica dalla barra laterale.")
        return None
    selected_key = f"selected_{key}"
    selected = st.session_state.get(selected_key)
    st.markdown(f"**{label} — seleziona dalla libreria**")
    for i in range(0, min(len(lib), 20), 4):
        cols = st.columns(4)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(lib):
                with col:
                    try:
                        st.image(lib[idx], use_container_width=True)
                    except Exception:
                        st.write(Path(lib[idx]).name)
                    if st.button("Seleziona", key=f"sel_{key}_{idx}"):
                        st.session_state[selected_key] = lib[idx]
                        st.rerun()
    if selected:
        st.markdown(f"✅ Selezionato: **{Path(selected).name}**")
    return selected


def _file_or_upload(label, key, accept=None, kind="photos", library_key="library_images"):
    c1, c2 = st.columns([1, 1])
    with c1:
        uploaded = st.file_uploader(f"Carica {label}", type=accept, key=f"upl_{key}")
    with c2:
        path = st.text_input(f"Oppure percorso {label}", key=f"path_{key}")
    saved = _save_upload(uploaded, kind)
    if saved:
        return saved
    selected = _image_picker(label, key, library_key)
    if selected:
        return selected
    if path:
        resolved = Path(path).resolve()
        if resolved.is_file():
            return str(resolved)
        st.error(f"File non trovato: {path}")
    return ""


def _folder_or_uploads(label, key, accept=None, kind="photos", library_key="library_images"):
    c1, c2 = st.columns([1, 1])
    with c1:
        uploaded = st.file_uploader(
            f"Carica {label} (multiplo)", accept_multiple_files=True, type=accept, key=f"upl_{key}"
        )
    with c2:
        folder = st.text_input(f"Oppure cartella {label}", key=f"path_{key}")
    if uploaded:
        paths = _save_uploads(uploaded, kind)
        _refresh_library()
        return str(Path(paths[0]).parent.resolve())
    lib = st.session_state.get(library_key, [])
    options = [""] + lib
    selected = st.selectbox(f"Oppure seleziona un file {label} dalla libreria", options, key=f"libsel_{key}")
    if selected:
        return str(Path(selected).resolve())
    if folder:
        resolved = Path(folder).resolve()
        if resolved.is_dir():
            return str(resolved)
        st.error(f"Cartella non trovata: {folder}")
    return ""


def _list_files(folder, exts):
    p = Path(folder)
    if not p.is_dir():
        return []
    return sorted([str(f) for f in p.iterdir() if f.suffix.lower() in exts and f.is_file()])


# ── BARRA LATERALE ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎬 AppFoto Studio Pro")
    st.markdown(
        '<span class="ai-badge">AI Integrata</span> '
        '<span class="tool-badge">FFmpeg</span> '
        '<span class="tool-badge">OpenCV</span>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("#### 📁 Libreria Media")
    img_uploads = st.file_uploader(
        "📸 Carica foto",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
        key="lib_img_uploader",
    )
    if img_uploads:
        paths = _save_uploads(img_uploads, "photos")
        for p in paths:
            db.log_upload(auth.current_user_id(), Path(p).name, p)

    vid_uploads = st.file_uploader(
        "🎥 Carica video",
        accept_multiple_files=True,
        type=["mp4", "mov", "avi", "mkv"],
        key="lib_vid_uploader",
    )
    if vid_uploads:
        paths = _save_uploads(vid_uploads, "videos")
        for p in paths:
            db.log_upload(auth.current_user_id(), Path(p).name, p)

    music_uploads = st.file_uploader(
        "🎵 Carica musica",
        accept_multiple_files=True,
        type=["mp3", "wav", "aac", "flac", "ogg", "m4a"],
        key="lib_music_uploader",
    )
    if music_uploads:
        paths = _save_uploads(music_uploads, "music")
        for p in paths:
            db.log_upload(auth.current_user_id(), Path(p).name, p)

    imgs, vids, music = _refresh_library()
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("📸 Foto", len(imgs))
    c2.metric("🎥 Video", len(vids))
    c3.metric("🎵 Musica", len(music))

    if imgs:
        with st.expander(f"📸 Anteprime foto ({len(imgs)})", expanded=False):
            for i in range(0, min(len(imgs), 9), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(imgs):
                        with col:
                            try:
                                st.image(imgs[i + j], use_container_width=True)
                            except Exception:
                                st.write(Path(imgs[i + j]).name)
    if vids:
        with st.expander(f"🎥 Video ({len(vids)})", expanded=False):
            for v in vids:
                st.write(f"📹 {Path(v).name}")
    if music:
        with st.expander(f"🎵 Brani ({len(music)})", expanded=False):
            for m in music:
                st.write(f"♫ {Path(m).name}")

    st.divider()
    ai_status = "✅ Configurata" if ai_tools.is_configured() else "❌ Non configurata"
    st.markdown(f"**🤖 OpenAI:** {ai_status}")
    st.markdown(f"**👤 Utente:** {st.session_state.get('username', '?')}")


# ── TABS PRINCIPALI ──────────────────────────────────────────────────────────
tabs = st.tabs([
    "🏠 Dashboard",
    "📸 Editor Foto",
    "🎬 Editor Video",
    "🎥 Slideshow",
    "🔗 Unisci Video",
    "🤖 AI Studio",
    "🔍 Duplicati",
    "✨ Migliora",
    "👤 Face Swap",
    "🎵 Musica",
    "📁 Lavori",
    "📊 Riepilogo",
    "🎨 Photopea",
    "⚙️ Admin",
    "📜 Storico",
])


# ═══════════════════════════════════════════════════════════════════════════
# 🏠 TAB 0 — DASHBOARD PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown("## 🏠 Dashboard Professionale")
    imgs, vids, music_list = _refresh_library()
    edited_photos = library.list_edited("photos")
    edited_videos = library.list_edited("videos")

    # ── Metriche rapide ──
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown('<div class="stat-card"><h3>📸</h3><h3>' + str(len(imgs)) + '</h3><p>Foto originali</p></div>', unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="stat-card"><h3>🎥</h3><h3>' + str(len(vids)) + '</h3><p>Video originali</p></div>', unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="stat-card"><h3>🎵</h3><h3>' + str(len(music_list)) + '</h3><p>Brani musicali</p></div>', unsafe_allow_html=True)
    with m4:
        st.markdown('<div class="stat-card"><h3>✏️</h3><h3>' + str(len(edited_photos)) + '</h3><p>Foto modificate</p></div>', unsafe_allow_html=True)
    with m5:
        st.markdown('<div class="stat-card"><h3>🎞️</h3><h3>' + str(len(edited_videos)) + '</h3><p>Video prodotti</p></div>', unsafe_allow_html=True)

    total_size = sum(f.stat().st_size for f in library.BASE.rglob("*") if f.is_file())
    st.metric("💾 Spazio occupato totale", f"{total_size / (1024 * 1024):.1f} MB")

    st.divider()

    # ── 📸 FOTO ORIGINALI — Carica e sfoglia ──
    st.markdown("### 📸 Foto Originali")
    dash_photo_uploads = st.file_uploader(
        "➕ Carica foto nella libreria",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png", "webp", "bmp", "tiff", "gif"],
        key="dash_photo_upload",
    )
    if dash_photo_uploads:
        saved = _save_uploads(dash_photo_uploads, "photos")
        for p in saved:
            db.log_upload(auth.current_user_id(), Path(p).name, p)
        imgs, vids, music_list = _refresh_library()
        st.success(f"✅ {len(saved)} foto caricate nella libreria!")

    # Risolvi solo file realmente presenti su disco
    imgs = library.resolve_media_paths(imgs, "photos")
    st.session_state.library_images = imgs

    if imgs:
        st.markdown(f"**{len(imgs)} foto in libreria** — clicca per selezionare")
        for row_start in range(0, len(imgs), 5):
            row_cols = st.columns(5)
            for j, col in enumerate(row_cols):
                idx = row_start + j
                if idx < len(imgs):
                    with col:
                        try:
                            st.image(imgs[idx], use_container_width=True)
                        except Exception:
                            st.caption(f"⚠️ Non apribile: {Path(imgs[idx]).name}")
                        st.caption(Path(imgs[idx]).name)
                        if st.button("📸 Seleziona", key=f"dash_sel_img_{idx}"):
                            st.session_state["dash_selected_photo"] = imgs[idx]
                            st.rerun()
        if st.session_state.get("dash_selected_photo"):
            st.info(f"✅ Foto selezionata: **{Path(st.session_state['dash_selected_photo']).name}** — disponibile in Editor Foto e altri strumenti")
    else:
        st.info("Nessuna foto in libreria. Carica le tue foto qui sopra — resteranno disponibili sempre.")

    st.divider()

    # ── 🎥 VIDEO ORIGINALI — Carica e sfoglia ──
    st.markdown("### 🎥 Video Originali")
    dash_video_uploads = st.file_uploader(
        "➕ Carica video nella libreria",
        accept_multiple_files=True,
        type=["mp4", "mov", "avi", "mkv", "flv", "wmv"],
        key="dash_video_upload",
    )
    if dash_video_uploads:
        saved = _save_uploads(dash_video_uploads, "videos")
        for p in saved:
            db.log_upload(auth.current_user_id(), Path(p).name, p)
        imgs, vids, music_list = _refresh_library()
        st.success(f"✅ {len(saved)} video caricati nella libreria!")

    if vids:
        st.markdown(f"**{len(vids)} video in libreria** — clicca per selezionare")
        for row_start in range(0, len(vids), 3):
            row_cols = st.columns(3)
            for j, col in enumerate(row_cols):
                idx = row_start + j
                if idx < len(vids):
                    with col:
                        st.video(vids[idx])
                        st.caption(Path(vids[idx]).name)
                        if st.button("🎥 Seleziona", key=f"dash_sel_vid_{idx}"):
                            st.session_state["dash_selected_video"] = vids[idx]
                            st.rerun()
        if st.session_state.get("dash_selected_video"):
            st.info(f"✅ Video selezionato: **{Path(st.session_state['dash_selected_video']).name}** — disponibile in Editor Video e altri strumenti")
    else:
        st.info("Nessun video in libreria. Carica i tuoi video qui sopra — resteranno disponibili sempre.")

    st.divider()

    # ── 🎵 MUSICA — Carica e sfoglia ──
    st.markdown("### 🎵 Brani Musicali")
    dash_music_uploads = st.file_uploader(
        "➕ Carica musica nella libreria",
        accept_multiple_files=True,
        type=["mp3", "wav", "aac", "flac", "ogg", "m4a"],
        key="dash_music_upload",
    )
    if dash_music_uploads:
        saved = _save_uploads(dash_music_uploads, "music")
        for p in saved:
            db.log_upload(auth.current_user_id(), Path(p).name, p)
        imgs, vids, music_list = _refresh_library()
        st.success(f"✅ {len(saved)} brani caricati nella libreria!")

    if music_list:
        for m in music_list:
            mc1, mc2 = st.columns([3, 1])
            with mc1:
                st.audio(m)
            with mc2:
                st.caption(Path(m).name)
    else:
        st.info("Nessun brano in libreria. Carica la tua musica qui sopra.")

    st.divider()

    # ── 🛠️ Strumenti disponibili ──
    st.markdown("### 🛠️ Strumenti disponibili")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="pro-card">
            <h4>📸 Editing Foto</h4>
            <p>Ritocco professionale con livelli, curve, HSL, colore selettivo,
            fusione immagini, testo, cornici, riduzione rumore,
            bilanciamento bianco, vignettatura, duotono, tilt-shift e altro.</p>
            <span class="tool-badge">Livelli Pro</span>
            <span class="tool-badge">Curve</span>
            <span class="tool-badge">HSL</span>
            <span class="tool-badge">Blend</span>
            <span class="tool-badge">Testo</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="pro-card">
            <h4>🎬 Editing Video</h4>
            <p>Montaggio professionale con timeline multi-clip, transizioni,
            color grading, testi/titoli, velocità, PiP, chroma key,
            stabilizzazione, dissolvenze, watermark e controllo audio.</p>
            <span class="tool-badge">Timeline</span>
            <span class="tool-badge">Transizioni</span>
            <span class="tool-badge">Color Grading</span>
            <span class="tool-badge">Chroma Key</span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="pro-card">
            <h4>🤖 AI Studio</h4>
            <p>Genera immagini con DALL-E 3, analizza foto con GPT-4o Vision,
            ottieni suggerimenti di miglioramento, genera didascalie
            per social media, chatta con l'assistente AI esperto.</p>
            <span class="ai-badge">DALL-E 3</span>
            <span class="ai-badge">GPT-4o Vision</span>
            <span class="ai-badge">Assistente AI</span>
        </div>
        """, unsafe_allow_html=True)

    user_id = auth.current_user_id()
    if user_id:
        jobs = db.list_jobs(user_id)[:5]
        if jobs:
            st.divider()
            st.markdown("### 📋 Ultimi lavori")
            for j in jobs:
                st.write(f"🔹 **{j[1]}** — {str(j[2])[:60]} — _{j[4]}_")


# ═══════════════════════════════════════════════════════════════════════════
# 📸 TAB 1 — EDITOR FOTO PRO
# ═══════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("## 📸 Editor Foto Professionale")
    st.markdown("Ritocco a livello professionale: livelli, curve, HSL, fusione, testo e molto altro.")

    c1, c2 = st.columns(2)
    with c1:
        edit_input = _file_or_upload(
            "foto", "edit_input",
            accept=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
            kind="photos", library_key="library_images",
        )
    with c2:
        edit_default = ""
        if edit_input:
            p = Path(edit_input)
            edit_default = str(library.EXPORTS / f"{p.stem}_pro{p.suffix}")
        edit_output = st.text_input("Foto in uscita", value=edit_default, key="edit_output")

    placeholder = np.full((300, 400, 3), 35, dtype=np.uint8)
    if edit_input:
        p = Path(edit_input).resolve()
        if p.is_file():
            try:
                preview_img = photo_editor.load_image(str(p))
                hist_img = photo_editor.generate_histogram(preview_img)
                col_img, col_hist = st.columns([3, 1])
                with col_img:
                    st.image(preview_img, caption="Originale", use_container_width=True)
                with col_hist:
                    st.image(hist_img, caption="Istogramma RGB", use_container_width=True)
            except Exception as e:
                st.error(f"Impossibile caricare: {e}")
                st.image(placeholder, caption="Errore", use_container_width=True)
        else:
            st.image(placeholder, caption="File non trovato", use_container_width=True)
    else:
        st.image(placeholder, caption="Seleziona o carica un'immagine", use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎚️ Regolazioni Base")
    c3, c4, c5, c6 = st.columns(4)
    with c3:
        edit_rotate = st.number_input("Rotazione (°)", value=0.0, step=90.0, key="edit_rotate")
    with c4:
        edit_width = st.number_input("Larghezza (px)", value=0, step=10, key="edit_width", help="0 = invariata")
    with c5:
        edit_height = st.number_input("Altezza (px)", value=0, step=10, key="edit_height", help="0 = invariata")
    with c6:
        edit_keep_aspect = st.checkbox("Mantieni proporzioni", value=True, key="edit_keep_aspect")

    c7, c8, c9, c10 = st.columns(4)
    with c7:
        edit_brightness = st.slider("☀️ Luminosità", 0.0, 3.0, 1.0, 0.05, key="edit_brightness")
    with c8:
        edit_contrast = st.slider("◐ Contrasto", 0.0, 3.0, 1.0, 0.05, key="edit_contrast")
    with c9:
        edit_saturation = st.slider("🎨 Saturazione", 0.0, 3.0, 1.0, 0.05, key="edit_saturation")
    with c10:
        edit_sharpen = st.slider("🔍 Nitidezza", 0.0, 2.0, 0.0, 0.1, key="edit_sharpen")

    c11, c12 = st.columns(2)
    with c11:
        edit_filter = st.selectbox(
            "🎭 Filtro",
            ["nessuno", "grayscale", "sepia", "blur", "sharpen", "emboss", "edge", "contour"],
            key="edit_filter",
        )
    with c12:
        edit_mirror_h = st.checkbox("↔️ Specchio orizzontale", key="edit_mirror_h")
        edit_mirror_v = st.checkbox("↕️ Specchio verticale", key="edit_mirror_v")

    # ── Livelli & Curve ──
    with st.expander("📊 Livelli & Curve", expanded=False):
        st.markdown("**Livelli di input** (punto nero, punto bianco, gamma)")
        lv1, lv2, lv3 = st.columns(3)
        with lv1:
            levels_black = st.slider("Punto nero", 0, 128, 0, key="levels_black")
        with lv2:
            levels_white = st.slider("Punto bianco", 128, 255, 255, key="levels_white")
        with lv3:
            levels_gamma = st.slider("Gamma livelli", 0.2, 3.0, 1.0, 0.05, key="levels_gamma")

        st.markdown("**Curve tonali**")
        edit_curve_shadow = st.slider("Ombre (curve)", 0, 128, 0, key="edit_curve_shadow")
        edit_curve_highlight = st.slider("Luci (curve)", 128, 255, 255, key="edit_curve_highlight")

    # ── Bilanciamento colore ──
    with st.expander("🎨 Bilanciamento Colore RGB", expanded=False):
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.markdown("**Ombre**")
            cb_shadow_r = st.slider("R ombre", -50, 50, 0, key="cb_sr")
            cb_shadow_g = st.slider("G ombre", -50, 50, 0, key="cb_sg")
            cb_shadow_b = st.slider("B ombre", -50, 50, 0, key="cb_sb")
        with bc2:
            st.markdown("**Mezzitoni**")
            cb_mid_r = st.slider("R mezzitoni", -50, 50, 0, key="cb_mr")
            cb_mid_g = st.slider("G mezzitoni", -50, 50, 0, key="cb_mg")
            cb_mid_b = st.slider("B mezzitoni", -50, 50, 0, key="cb_mb")
        with bc3:
            st.markdown("**Luci**")
            cb_high_r = st.slider("R luci", -50, 50, 0, key="cb_hr")
            cb_high_g = st.slider("G luci", -50, 50, 0, key="cb_hg")
            cb_high_b = st.slider("B luci", -50, 50, 0, key="cb_hb")

    # ── HSL & Vibranza ──
    with st.expander("🌈 HSL & Vibranza", expanded=False):
        h1, h2, h3 = st.columns(3)
        with h1:
            edit_hue = st.slider("Tonalità", -180, 180, 0, key="edit_hue")
        with h2:
            edit_hsl_sat = st.slider("Saturazione HSL", 0.0, 2.0, 1.0, 0.1, key="edit_hsl_sat")
        with h3:
            edit_light = st.slider("Luminosità HSL", -0.5, 0.5, 0.0, 0.05, key="edit_light")
        edit_vibrance = st.slider("Vibranza", -1.0, 1.0, 0.0, 0.1, key="edit_vibrance")

    # ── Effetti avanzati ──
    with st.expander("✨ Effetti Avanzati", expanded=False):
        ef1, ef2 = st.columns(2)
        with ef1:
            edit_vignette = st.slider("Vignettatura", 0.0, 1.0, 0.0, 0.05, key="edit_vignette")
            edit_noise_red = st.slider("Riduzione rumore", 0, 15, 0, key="edit_noise_red")
            edit_auto_wb = st.checkbox("🎯 Bilanciamento bianco automatico", key="edit_auto_wb")
        with ef2:
            edit_dodge = st.slider("Dodge (schiarisci)", 0.0, 1.0, 0.0, 0.05, key="edit_dodge")
            edit_burn = st.slider("Burn (scurisci)", 0.0, 1.0, 0.0, 0.05, key="edit_burn")
            edit_tilt_shift = st.checkbox("📷 Effetto tilt-shift", key="edit_tilt_shift")

        edit_duotone = st.checkbox("🎭 Duotono", key="edit_duotone")
        if edit_duotone:
            dt1, dt2 = st.columns(2)
            with dt1:
                edit_dt1 = st.color_picker("Colore ombre", "#1a1a1a", key="edit_dt1")
            with dt2:
                edit_dt2 = st.color_picker("Colore luci", "#f2c94c", key="edit_dt2")

        edit_gradient = st.checkbox("🌅 Mappa gradiente", key="edit_gradient")
        if edit_gradient:
            gm1, gm2, gm3 = st.columns(3)
            with gm1:
                grad_c1 = st.color_picker("Colore 1", "#001122", key="grad_c1")
            with gm2:
                grad_c2 = st.color_picker("Colore 2", "#ff9900", key="grad_c2")
            with gm3:
                grad_opacity = st.slider("Opacità gradiente", 0.0, 1.0, 0.3, 0.05, key="grad_opacity")

    # ── Testo & Watermark ──
    with st.expander("📝 Testo & Watermark", expanded=False):
        txt_content = st.text_input("Testo da sovrapporre", key="txt_content")
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            txt_size = st.number_input("Dimensione font", value=48, min_value=8, max_value=200, key="txt_size")
        with tc2:
            txt_color = st.color_picker("Colore testo", "#ffffff", key="txt_color")
        with tc3:
            txt_shadow = st.checkbox("Ombra testo", value=True, key="txt_shadow")
        tp1, tp2 = st.columns(2)
        with tp1:
            txt_x = st.number_input("Posizione X", value=50, min_value=0, key="txt_x")
        with tp2:
            txt_y = st.number_input("Posizione Y", value=50, min_value=0, key="txt_y")

        st.divider()
        wm_text = st.text_input("Watermark", value="© AppFoto Studio", key="wm_text")
        wm_pos = st.selectbox("Posizione watermark", ["bottom-right", "bottom-left", "top-right", "top-left", "center"], key="wm_pos")

    # ── Cornice & Bordo ──
    with st.expander("🖼️ Cornice & Bordo", expanded=False):
        border_w = st.slider("Larghezza bordo (px)", 0, 100, 0, key="border_w")
        border_color = st.color_picker("Colore bordo", "#ffffff", key="border_color")
        border_style = st.selectbox("Stile bordo", ["solid", "double"], key="border_style")

    # ── Fusione immagini ──
    with st.expander("🔀 Fusione Immagini (Blend)", expanded=False):
        blend_img = _file_or_upload(
            "seconda immagine", "blend_img",
            accept=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
            kind="photos", library_key="library_images",
        )
        blend_mode = st.selectbox(
            "Modalità fusione",
            ["normal", "multiply", "screen", "overlay", "soft_light", "hard_light",
             "difference", "exclusion", "color_dodge", "color_burn"],
            key="blend_mode",
        )
        blend_opacity = st.slider("Opacità fusione", 0.0, 1.0, 0.5, 0.05, key="blend_opacity")

    def _build_edit_kwargs():
        kwargs = {
            "rotate": edit_rotate,
            "brightness": edit_brightness,
            "contrast": edit_contrast,
            "saturation": edit_saturation,
            "sharpen": edit_sharpen,
            "mirror_h": edit_mirror_h,
            "mirror_v": edit_mirror_v,
        }
        if edit_width:
            kwargs["width"] = edit_width
        if edit_height:
            kwargs["height"] = edit_height
        kwargs["keep_aspect"] = edit_keep_aspect
        if edit_filter != "nessuno":
            kwargs["filter"] = edit_filter
        if levels_black != 0 or levels_white != 255 or levels_gamma != 1.0:
            kwargs["levels"] = {"black": levels_black, "white": levels_white, "gamma": levels_gamma}
        if edit_curve_shadow != 0 or edit_curve_highlight != 255:
            kwargs["curves"] = [(0, edit_curve_shadow), (128, 128), (255, edit_curve_highlight)]
        cbs = (cb_shadow_r, cb_shadow_g, cb_shadow_b)
        cbm = (cb_mid_r, cb_mid_g, cb_mid_b)
        cbh = (cb_high_r, cb_high_g, cb_high_b)
        if any(v != 0 for v in cbs + cbm + cbh):
            kwargs["color_balance"] = (cbs, cbm, cbh)
        if edit_hue != 0 or edit_hsl_sat != 1.0 or edit_light != 0.0:
            kwargs["hsl"] = (edit_hue, edit_hsl_sat, edit_light)
        if edit_vibrance != 0:
            kwargs["vibrance"] = edit_vibrance
        if edit_vignette != 0:
            kwargs["vignette"] = edit_vignette
        if edit_duotone:
            kwargs["duotone"] = (edit_dt1, edit_dt2)
        if edit_noise_red > 0:
            kwargs["noise_reduction"] = edit_noise_red
        if edit_auto_wb:
            kwargs["auto_wb"] = True
        if edit_dodge > 0:
            kwargs["dodge"] = {"amount": edit_dodge}
        if edit_burn > 0:
            kwargs["burn"] = {"amount": edit_burn}
        if border_w > 0:
            c = tuple(int(border_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
            kwargs["border"] = {"width": border_w, "color": c}
        if txt_content:
            c = tuple(int(txt_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
            kwargs["text"] = {
                "content": txt_content, "position": (txt_x, txt_y),
                "font_size": txt_size, "color": c, "shadow": txt_shadow, "opacity": 255,
            }
        if edit_gradient:
            kwargs["gradient_map"] = (grad_c1, grad_c2, grad_opacity)
        return kwargs

    st.markdown("---")
    c_prev, c_save = st.columns(2)
    with c_prev:
        preview_btn = st.button("👁️ Anteprima in tempo reale", key="edit_preview", use_container_width=True)
    with c_save:
        save_btn = st.button("💾 Salva modifiche", key="edit_save", use_container_width=True)

    if preview_btn:
        if not edit_input:
            st.error("Seleziona una foto prima")
        else:
            with st.spinner("Generazione anteprima..."):
                try:
                    preview_path = str(library.EDITED_PHOTOS / f"preview_{Path(edit_input).stem}.jpg")
                    photo_editor.process_image(edit_input, preview_path, **_build_edit_kwargs())
                    result_img = photo_editor.load_image(preview_path)

                    if blend_img:
                        blend_src = photo_editor.load_image(blend_img)
                        result_img = photo_editor.blend_images(result_img, blend_src, blend_mode, blend_opacity)

                    if edit_tilt_shift:
                        result_img = photo_editor.apply_tilt_shift(result_img)

                    if wm_text:
                        result_img = photo_editor.add_watermark(result_img, wm_text, wm_pos)

                    col_before, col_after = st.columns(2)
                    with col_before:
                        st.image(photo_editor.load_image(edit_input), caption="🔹 Prima", use_container_width=True)
                    with col_after:
                        st.image(result_img, caption="🔸 Dopo", use_container_width=True)

                    new_hist = photo_editor.generate_histogram(result_img)
                    st.image(new_hist, caption="Istogramma risultato", width=400)
                except Exception as e:
                    st.error(str(e))

    if save_btn:
        if not edit_input or not edit_output:
            st.error("Inserisci foto in ingresso e in uscita")
        else:
            with st.spinner("Salvataggio..."):
                try:
                    out_path = library.next_version(edit_output)
                    photo_editor.process_image(edit_input, out_path, **_build_edit_kwargs())
                    result_img = photo_editor.load_image(out_path)

                    if blend_img:
                        blend_src = photo_editor.load_image(blend_img)
                        result_img = photo_editor.blend_images(result_img, blend_src, blend_mode, blend_opacity)
                        photo_editor.save_image(result_img, out_path)

                    if edit_tilt_shift:
                        result_img = photo_editor.apply_tilt_shift(result_img)
                        photo_editor.save_image(result_img, out_path)

                    if wm_text:
                        result_img = photo_editor.add_watermark(result_img, wm_text, wm_pos)
                        photo_editor.save_image(result_img, out_path)

                    st.image(result_img, caption="✅ Risultato salvato", use_container_width=True)
                    st.success(f"Foto salvata in: {out_path}")
                    _log("photo_edit_pro", edit_input, out_path, "ok")
                    _refresh_library()
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════
# 🎬 TAB 2 — EDITOR VIDEO PRO
# ═══════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("## 🎬 Editor Video Professionale")
    st.markdown("Montaggio a livello cinematografico con timeline, transizioni, color grading e molto altro.")

    vid_operation = st.selectbox(
        "🎯 Operazione",
        [
            "✂️ Taglia",
            "⏩ Velocità",
            "🔄 Inverti Video",
            "🎵 Aggiungi Musica",
            "🔊 Volume Audio",
            "🎨 Applica Filtro",
            "🎬 Color Grading",
            "📝 Testo / Titoli",
            "🌅 Dissolvenza (Fade)",
            "📺 Picture-in-Picture",
            "🟩 Chroma Key (Green Screen)",
            "📐 Stabilizzazione",
            "💧 Watermark Video",
            "🎞️ Timeline Multi-Clip",
            "📸 Estrai Frame",
            "🔈 Estrai Audio",
            "ℹ️ Info Video",
        ],
        key="vid_op",
    )

    if vid_operation != "🎞️ Timeline Multi-Clip":
        c1, c2 = st.columns(2)
        with c1:
            vid_input = _file_or_upload(
                "video", "vid_input",
                accept=["mp4", "mov", "avi", "mkv"],
                kind="videos", library_key="library_videos",
            )
        with c2:
            vid_output = st.text_input(
                "File di uscita",
                value=str(library.EDITED_VIDEOS / "output_pro_v1.mp4"),
                key="vid_output",
            )

        if vid_input and Path(vid_input).is_file():
            info = video_editor.get_video_info(vid_input)
            if info:
                info_cols = st.columns(len(info))
                for i, (k, v) in enumerate(info.items()):
                    with info_cols[i % len(info_cols)]:
                        st.caption(f"**{k}:** {v}")

    # ── Taglia ──
    if vid_operation == "✂️ Taglia":
        c3, c4 = st.columns(2)
        with c3:
            start_t = st.number_input("Inizio (s)", value=0.0, min_value=0.0, step=0.1, key="vid_start")
        with c4:
            end_t = st.number_input("Fine (s)", value=10.0, min_value=0.0, step=0.1, key="vid_end")
        if st.button("✂️ Taglia video", key="vid_trim"):
            with st.spinner("Taglio in corso..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.trim_video(vid_input, out_path, start_t, end_t)
                    st.success(f"Video tagliato: {out_path}")
                    st.video(out_path)
                    _log("video_trim", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Velocità ──
    elif vid_operation == "⏩ Velocità":
        speed = st.slider(
            "Velocità (0.25 = rallentato 4x, 2.0 = veloce 2x, 4.0 = veloce 4x)",
            0.25, 4.0, 1.0, 0.25, key="vid_speed",
        )
        speed_labels = {0.25: "🐌 Super Slow Motion", 0.5: "🐢 Slow Motion", 1.0: "▶️ Normale",
                        2.0: "⏩ Veloce 2x", 3.0: "⏩ Veloce 3x", 4.0: "⚡ Veloce 4x"}
        st.info(speed_labels.get(speed, f"⏩ Velocità {speed}x"))
        if st.button("⏩ Applica velocità", key="vid_speed_btn"):
            with st.spinner("Modifica velocità..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.change_speed(vid_input, out_path, speed)
                    st.success(f"Video con velocità {speed}x: {out_path}")
                    st.video(out_path)
                    _log("video_speed", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Inverti ──
    elif vid_operation == "🔄 Inverti Video":
        rev_audio = st.checkbox("Inverti anche l'audio", value=True, key="rev_audio")
        st.warning("⚠️ L'inversione richiede che il video sia caricato interamente in memoria.")
        if st.button("🔄 Inverti video", key="vid_reverse"):
            with st.spinner("Inversione in corso..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.reverse_video(vid_input, out_path, rev_audio)
                    st.success(f"Video invertito: {out_path}")
                    st.video(out_path)
                    _log("video_reverse", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Aggiungi Musica ──
    elif vid_operation == "🎵 Aggiungi Musica":
        audio_file = st.selectbox("🎵 File audio", [""] + library.list_music(), key="vid_audio")
        loop_audio = st.checkbox("🔁 Ripeti audio se più corto del video", key="vid_loop")
        if st.button("🎵 Aggiungi musica", key="vid_music_btn"):
            with st.spinner("Aggiunta audio..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.add_music_to_video(vid_input, audio_file, out_path, loop_audio)
                    st.success(f"Audio aggiunto: {out_path}")
                    st.video(out_path)
                    _log("video_music", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Volume Audio ──
    elif vid_operation == "🔊 Volume Audio":
        volume = st.slider("Volume (1.0 = originale)", 0.0, 5.0, 1.0, 0.1, key="vid_volume")
        if st.button("🔊 Applica volume", key="vid_vol_btn"):
            with st.spinner("Regolazione volume..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.adjust_volume(vid_input, out_path, volume)
                    st.success(f"Volume regolato: {out_path}")
                    st.video(out_path)
                    _log("video_volume", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Applica Filtro ──
    elif vid_operation == "🎨 Applica Filtro":
        filter_name = st.selectbox(
            "Filtro",
            ["grayscale", "blur", "negate", "edgedetect", "vignette", "sharpen"],
            key="vid_filter",
        )
        if st.button("🎨 Applica filtro", key="vid_filter_btn"):
            with st.spinner("Applicazione filtro..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.apply_filter(vid_input, out_path, filter_name)
                    st.success(f"Filtro applicato: {out_path}")
                    st.video(out_path)
                    _log("video_filter", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Color Grading ──
    elif vid_operation == "🎬 Color Grading":
        st.markdown("### 🎬 Color Grading Professionale")
        cg1, cg2, cg3 = st.columns(3)
        with cg1:
            cg_brightness = st.slider("☀️ Luminosità", -1.0, 1.0, 0.0, 0.05, key="cg_brightness")
            cg_contrast = st.slider("◐ Contrasto", 0.0, 3.0, 1.0, 0.05, key="cg_contrast")
        with cg2:
            cg_saturation = st.slider("🎨 Saturazione", 0.0, 3.0, 1.0, 0.05, key="cg_saturation")
            cg_gamma = st.slider("🔆 Gamma", 0.2, 3.0, 1.0, 0.05, key="cg_gamma")
        with cg3:
            cg_temperature = st.slider("🌡️ Temperatura", -1.0, 1.0, 0.0, 0.05, key="cg_temperature")
            cg_exposure = st.slider("📸 Esposizione (EV)", -3.0, 3.0, 0.0, 0.1, key="cg_exposure")
        if st.button("🎬 Applica color grading", key="cg_apply"):
            with st.spinner("Color grading in corso..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.color_grade_video(
                        vid_input, out_path,
                        brightness=cg_brightness, contrast=cg_contrast,
                        saturation=cg_saturation, temperature=cg_temperature,
                        gamma=cg_gamma, exposure=cg_exposure,
                    )
                    st.success(f"Color grading applicato: {out_path}")
                    st.video(out_path)
                    _log("video_colorgrade", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Testo / Titoli ──
    elif vid_operation == "📝 Testo / Titoli":
        st.markdown("### 📝 Sovrapponi Testo / Titoli")
        title_text = st.text_input("Testo del titolo", value="Il mio film", key="title_text")
        tt1, tt2, tt3 = st.columns(3)
        with tt1:
            title_pos = st.selectbox(
                "Posizione",
                ["center", "top", "bottom", "top-left", "top-right", "bottom-left", "bottom-right"],
                key="title_pos",
            )
        with tt2:
            title_size = st.number_input("Dimensione font", value=56, min_value=12, max_value=200, key="title_size")
        with tt3:
            title_color = st.selectbox("Colore", ["white", "yellow", "red", "green", "blue", "cyan"], key="title_color")
        tt4, tt5 = st.columns(2)
        with tt4:
            title_start = st.number_input("Inizio (s)", value=0.0, min_value=0.0, step=0.5, key="title_start")
        with tt5:
            title_dur = st.number_input("Durata (s, 0 = tutto il video)", value=0.0, min_value=0.0, step=0.5, key="title_dur")
        if st.button("📝 Aggiungi titolo", key="title_apply"):
            with st.spinner("Aggiunta titolo..."):
                try:
                    out_path = library.next_version(vid_output)
                    dur = title_dur if title_dur > 0 else None
                    video_editor.add_text_overlay(
                        vid_input, out_path, title_text,
                        position=title_pos, font_size=title_size,
                        color=title_color, start_time=title_start, duration=dur,
                    )
                    st.success(f"Titolo aggiunto: {out_path}")
                    st.video(out_path)
                    _log("video_title", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Dissolvenza ──
    elif vid_operation == "🌅 Dissolvenza (Fade)":
        st.markdown("### 🌅 Dissolvenza in apertura e chiusura")
        fd1, fd2 = st.columns(2)
        with fd1:
            fade_in_v = st.number_input("Fade-in video (s)", value=0.0, min_value=0.0, step=0.5, key="fade_in_v")
            fade_in_a = st.number_input("Fade-in audio (s)", value=0.0, min_value=0.0, step=0.5, key="fade_in_a")
        with fd2:
            fade_out_v = st.number_input("Fade-out video (s)", value=0.0, min_value=0.0, step=0.5, key="fade_out_v")
            fade_out_a = st.number_input("Fade-out audio (s)", value=0.0, min_value=0.0, step=0.5, key="fade_out_a")
        if st.button("🌅 Applica dissolvenza", key="fade_apply"):
            with st.spinner("Applicazione dissolvenza..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.add_fade(
                        vid_input, out_path,
                        fade_in=fade_in_v, fade_out=fade_out_v,
                        audio_fade_in=fade_in_a, audio_fade_out=fade_out_a,
                    )
                    st.success(f"Dissolvenza applicata: {out_path}")
                    st.video(out_path)
                    _log("video_fade", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Picture-in-Picture ──
    elif vid_operation == "📺 Picture-in-Picture":
        st.markdown("### 📺 Picture-in-Picture")
        pip_overlay = _file_or_upload(
            "video overlay (PiP)", "pip_overlay",
            accept=["mp4", "mov", "avi", "mkv"],
            kind="videos", library_key="library_videos",
        )
        pp1, pp2 = st.columns(2)
        with pp1:
            pip_pos = st.selectbox("Posizione PiP", ["bottom-right", "bottom-left", "top-right", "top-left", "center"], key="pip_pos")
        with pp2:
            pip_scale = st.slider("Scala PiP", 0.1, 0.5, 0.25, 0.05, key="pip_scale")
        pip_start = st.number_input("Inizio PiP (s)", value=0.0, min_value=0.0, step=0.5, key="pip_start")
        if st.button("📺 Applica PiP", key="pip_apply"):
            with st.spinner("Applicazione Picture-in-Picture..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.picture_in_picture(
                        vid_input, pip_overlay, out_path,
                        position=pip_pos, scale=pip_scale, start_time=pip_start,
                    )
                    st.success(f"PiP applicato: {out_path}")
                    st.video(out_path)
                    _log("video_pip", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Chroma Key ──
    elif vid_operation == "🟩 Chroma Key (Green Screen)":
        st.markdown("### 🟩 Chroma Key - Rimozione sfondo")
        ck_bg = _file_or_upload(
            "sfondo sostitutivo (video/immagine)", "ck_bg",
            accept=["mp4", "mov", "avi", "mkv", "jpg", "jpeg", "png"],
            kind="videos", library_key="library_videos",
        )
        ck1, ck2, ck3 = st.columns(3)
        with ck1:
            ck_color = st.selectbox("Colore chiave", ["green", "blue", "red"], key="ck_color")
        with ck2:
            ck_sim = st.slider("Similarità", 0.01, 1.0, 0.3, 0.01, key="ck_sim")
        with ck3:
            ck_blend = st.slider("Blend bordi", 0.0, 0.3, 0.05, 0.01, key="ck_blend")
        if st.button("🟩 Applica Chroma Key", key="ck_apply"):
            with st.spinner("Rimozione sfondo..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.chroma_key(
                        vid_input, ck_bg, out_path,
                        color=ck_color, similarity=ck_sim, blend=ck_blend,
                    )
                    st.success(f"Chroma key applicato: {out_path}")
                    st.video(out_path)
                    _log("video_chromakey", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Stabilizzazione ──
    elif vid_operation == "📐 Stabilizzazione":
        st.markdown("### 📐 Stabilizzazione Video")
        st.info("Riduce le vibrazioni e i tremolii del video usando deshake di FFmpeg.")
        if st.button("📐 Stabilizza video", key="stab_apply"):
            with st.spinner("Stabilizzazione in corso..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.stabilize_video(vid_input, out_path)
                    st.success(f"Video stabilizzato: {out_path}")
                    st.video(out_path)
                    _log("video_stabilize", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Watermark Video ──
    elif vid_operation == "💧 Watermark Video":
        st.markdown("### 💧 Watermark Video")
        vwm_text = st.text_input("Testo watermark", value="AppFoto Studio", key="vwm_text")
        vw1, vw2, vw3 = st.columns(3)
        with vw1:
            vwm_pos = st.selectbox("Posizione", ["bottom-right", "bottom-left", "top-right", "top-left", "center"], key="vwm_pos")
        with vw2:
            vwm_size = st.number_input("Dimensione font", value=24, min_value=8, max_value=100, key="vwm_size")
        with vw3:
            vwm_opacity = st.slider("Opacità", 0.1, 1.0, 0.5, 0.05, key="vwm_opacity")
        if st.button("💧 Aggiungi watermark", key="vwm_apply"):
            with st.spinner("Aggiunta watermark..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.add_video_watermark(
                        vid_input, out_path, text=vwm_text,
                        position=vwm_pos, font_size=vwm_size, opacity=vwm_opacity,
                    )
                    st.success(f"Watermark aggiunto: {out_path}")
                    st.video(out_path)
                    _log("video_watermark", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Timeline Multi-Clip ──
    elif vid_operation == "🎞️ Timeline Multi-Clip":
        st.markdown("### 🎞️ Timeline Multi-Clip con Transizioni")
        st.markdown(
            "Assembla più clip in sequenza con transizioni professionali. "
            "Come in un software di montaggio video professionale."
        )
        tl_output = st.text_input(
            "File video finale",
            value=str(library.EDITED_VIDEOS / "timeline_v1.mp4"),
            key="tl_output",
        )
        tl1, tl2, tl3 = st.columns(3)
        with tl1:
            tl_transition = st.selectbox(
                "Transizione",
                ["fade", "wipeleft", "wiperight", "wipeup", "wipedown",
                 "slideleft", "slideright", "dissolve", "pixelize", "circleopen"],
                key="tl_transition",
            )
        with tl2:
            tl_trans_dur = st.number_input("Durata transizione (s)", value=0.5, min_value=0.1, step=0.1, key="tl_trans_dur")
        with tl3:
            tl_resolution = st.selectbox("Risoluzione", ["1920x1080", "1280x720", "3840x2160"], key="tl_resolution")

        num_clips = st.number_input("Numero di clip", value=2, min_value=2, max_value=20, key="tl_num_clips")
        clips_data = []
        for ci in range(int(num_clips)):
            with st.expander(f"🎬 Clip {ci + 1}", expanded=(ci < 3)):
                all_vids = st.session_state.get("library_videos", [])
                options = [""] + all_vids
                clip_path = st.selectbox(f"Video clip {ci+1}", options, key=f"tl_clip_{ci}")
                clip_upload = st.file_uploader(f"O carica clip {ci+1}", type=["mp4", "mov", "avi", "mkv"], key=f"tl_upl_{ci}")
                if clip_upload:
                    clip_path = _save_upload(clip_upload, "videos")
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    clip_start = st.number_input(f"Inizio (s)", value=0.0, min_value=0.0, step=0.5, key=f"tl_start_{ci}")
                with cc2:
                    clip_end = st.number_input(f"Fine (s, 0=tutto)", value=0.0, min_value=0.0, step=0.5, key=f"tl_end_{ci}")
                with cc3:
                    clip_speed = st.number_input(f"Velocità", value=1.0, min_value=0.25, max_value=4.0, step=0.25, key=f"tl_speed_{ci}")
                if clip_path:
                    cd = {"path": clip_path, "speed": clip_speed}
                    if clip_start > 0:
                        cd["start"] = clip_start
                    if clip_end > 0:
                        cd["end"] = clip_end
                    clips_data.append(cd)

        if st.button("🎞️ Assembla Timeline", key="tl_assemble"):
            if len(clips_data) < 2:
                st.error("Seleziona almeno 2 clip")
            else:
                with st.spinner(f"Assemblaggio di {len(clips_data)} clip con transizione {tl_transition}..."):
                    try:
                        out_path = library.next_version(tl_output)
                        video_editor.create_timeline(
                            clips_data, out_path,
                            transition=tl_transition,
                            transition_duration=tl_trans_dur,
                            resolution=tl_resolution,
                        )
                        st.success(f"🎬 Timeline assemblata: {out_path}")
                        st.video(out_path)
                        _log("video_timeline", f"{len(clips_data)} clips", out_path, "ok")
                    except Exception as e:
                        st.error(str(e))

    # ── Estrai Frame ──
    elif vid_operation == "📸 Estrai Frame":
        interval = st.number_input("Intervallo in secondi", value=1.0, min_value=0.1, step=0.1, key="vid_interval")
        if st.button("📸 Estrai frame", key="vid_frames"):
            with st.spinner("Estrazione frame..."):
                try:
                    video_editor.extract_frames(vid_input, vid_output, interval)
                    st.success(f"Frame estratti in: {vid_output}")
                    _log("video_frames", vid_input, vid_output, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Estrai Audio ──
    elif vid_operation == "🔈 Estrai Audio":
        audio_out = st.text_input("File audio di uscita", value=str(library.MUSIC / "extracted.mp3"), key="audio_out")
        if st.button("🔈 Estrai audio", key="extract_audio_btn"):
            with st.spinner("Estrazione audio..."):
                try:
                    out_path = library.next_version(audio_out)
                    video_editor.extract_audio(vid_input, out_path)
                    st.success(f"Audio estratto: {out_path}")
                    st.audio(out_path)
                    _log("extract_audio", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))

    # ── Info Video ──
    elif vid_operation == "ℹ️ Info Video":
        if vid_input and Path(vid_input).is_file():
            info = video_editor.get_video_info(vid_input)
            for k, v in info.items():
                st.write(f"**{k}:** {v}")
        else:
            st.info("Seleziona un video per vederne le informazioni.")


# ═══════════════════════════════════════════════════════════════════════════
# 🎥 TAB 3 — SLIDESHOW (iMovie / Canva / CapCut / Adobe Express)
# ═══════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("## 🎥 Slideshow Studio")
    st.markdown(
        "Crea video da foto con stile **iMovie**, **Canva**, **CapCut** e **Adobe Express** — "
        "musica, titoli, transizioni, filtri e formati social."
    )
    st.markdown(
        '<span class="tool-badge">iMovie</span> '
        '<span class="tool-badge">Canva</span> '
        '<span class="tool-badge">CapCut</span> '
        '<span class="tool-badge">Adobe Express</span>',
        unsafe_allow_html=True,
    )

    # ── Template stile programmi ──
    st.markdown("### 🎬 Scegli lo stile (template)")
    template_names = list(video_slideshow.TEMPLATES.keys())
    sld_template = st.selectbox(
        "Template professionale",
        ["Personalizzato"] + template_names,
        key="sld_template",
        help="Applica automaticamente durata, transizioni, filtri e formato come nei programmi originali.",
    )
    tmpl = video_slideshow.apply_template(sld_template) if sld_template != "Personalizzato" else None
    if tmpl:
        st.info(
            f"**{sld_template}** → durata {tmpl['duration']}s · "
            f"transizione `{tmpl['transition']}` · filtro `{tmpl['filter']}` · "
            f"formato {tmpl['aspect']}"
            + (" · Ken Burns ON" if tmpl.get("ken_burns") else "")
        )

    # ── Foto ──
    st.markdown("### 📸 Foto")
    sld_uploads = st.file_uploader(
        "➕ Carica foto (restano in libreria)",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
        key="sld_uploader",
    )
    if sld_uploads:
        saved = _save_uploads(sld_uploads, "photos")
        for p in saved:
            db.log_upload(auth.current_user_id(), Path(p).name, p)
        _refresh_library()
        st.success(f"✅ {len(saved)} foto caricate")

    lib_imgs = st.session_state.get("library_images", []) or library.list_originals("photos")
    name_to_path = {}
    for p in lib_imgs:
        resolved = library.resolve_media_path(p, "photos")
        if resolved:
            name_to_path[Path(resolved).name] = resolved

    if not name_to_path:
        st.warning("Nessuna foto in libreria. Caricale qui sopra.")
        sld_selected_names = []
    else:
        sld_selected_names = st.multiselect(
            f"Seleziona foto ({len(name_to_path)} disponibili) — ordine = ordine video",
            options=list(name_to_path.keys()),
            key="sld_multiselect",
        )
        if sld_selected_names:
            preview_cols = st.columns(min(5, len(sld_selected_names)))
            for i, name in enumerate(sld_selected_names[:10]):
                with preview_cols[i % len(preview_cols)]:
                    try:
                        st.image(name_to_path[name], use_container_width=True, caption=name)
                    except Exception:
                        st.caption(f"⚠️ {name}")

    # ── Musica (Canva / CapCut / iMovie / Adobe Express) ──
    st.markdown("### 🎵 Musica di sottofondo")
    st.caption("Come in iMovie, CapCut, Canva e Adobe Express: aggiungi una colonna sonora al video.")
    sld_music_up = st.file_uploader(
        "➕ Carica brano (mp3, wav, aac, m4a…)",
        type=["mp3", "wav", "aac", "flac", "ogg", "m4a"],
        key="sld_music_uploader",
    )
    if sld_music_up:
        mp = _save_upload(sld_music_up, "music")
        db.log_upload(auth.current_user_id(), Path(mp).name, mp)
        _refresh_library()
        st.success(f"✅ Musica caricata: {Path(mp).name}")
        st.session_state["sld_last_music"] = mp

    music_opts = library.list_music()
    default_music_idx = 0
    if st.session_state.get("sld_last_music") in music_opts:
        default_music_idx = music_opts.index(st.session_state["sld_last_music"]) + 1

    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        sld_music = st.selectbox(
            "Brano dalla libreria",
            [""] + music_opts,
            index=min(default_music_idx, len(music_opts)),
            format_func=lambda x: Path(x).name if x else "(nessuna musica)",
            key="sld_music",
        )
    with mc2:
        default_vol = tmpl["music_volume"] if tmpl else 0.8
        sld_music_vol = st.slider("Volume musica", 0.0, 1.5, float(default_vol), 0.05, key="sld_music_vol")
    with mc3:
        default_fade = tmpl["fade_audio"] if tmpl else 1.0
        sld_fade_audio = st.slider("Fade audio (s)", 0.0, 3.0, float(default_fade), 0.1, key="sld_fade_audio")
    if sld_music:
        st.audio(sld_music)

    # ── Titoli (Canva / Adobe Express / iMovie) ──
    st.markdown("### ✍️ Titoli e testo")
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        sld_title = st.text_input("Titolo principale", placeholder="Es: La nostra estate", key="sld_title")
    with tc2:
        sld_subtitle = st.text_input("Sottotitolo", placeholder="Es: Agosto 2026", key="sld_subtitle")
    with tc3:
        sld_title_pos = st.selectbox("Posizione titolo", ["center", "top", "bottom"], key="sld_title_pos")

    # ── Transizioni, filtri, formato ──
    st.markdown("### ✨ Transizioni, filtri e formato")
    default_trans = tmpl["transition"] if tmpl else "dissolvenza"
    default_filter = tmpl["filter"] if tmpl else "nessuno"
    default_dur = tmpl["duration"] if tmpl else 3.0
    default_tdur = tmpl["transition_dur"] if tmpl else 0.5
    default_kb = tmpl["ken_burns"] if tmpl else False
    default_aspect = tmpl["aspect"] if tmpl else "16:9"

    ec1, ec2, ec3, ec4 = st.columns(4)
    with ec1:
        trans_opts = list(video_slideshow.TRANSITIONS.keys())
        trans_idx = trans_opts.index(default_trans) if default_trans in trans_opts else 0
        sld_trans_type = st.selectbox("Transizione", trans_opts, index=trans_idx, key="sld_trans_type")
    with ec2:
        filter_opts = list(video_slideshow.FILTERS.keys())
        filt_idx = filter_opts.index(default_filter) if default_filter in filter_opts else 0
        sld_filter = st.selectbox("Filtro / Look", filter_opts, index=filt_idx, key="sld_filter")
    with ec3:
        aspect_opts = list(video_slideshow.ASPECT_RESOLUTIONS.keys())
        asp_idx = aspect_opts.index(default_aspect) if default_aspect in aspect_opts else 0
        sld_aspect = st.selectbox("Formato", aspect_opts, index=asp_idx, key="sld_aspect",
                                 help="16:9 YouTube · 9:16 Reels/TikTok · 1:1 Instagram · 4:5 Feed")
    with ec4:
        sld_ken_burns = st.checkbox("Ken Burns (zoom iMovie)", value=default_kb, key="sld_ken_burns")

    res_map = video_slideshow.ASPECT_RESOLUTIONS.get(sld_aspect, video_slideshow.ASPECT_RESOLUTIONS["16:9"])
    res_labels = list(res_map.keys())
    pc1, pc2, pc3, pc4 = st.columns(4)
    with pc1:
        sld_duration = st.number_input("Durata foto (s)", value=float(default_dur), min_value=0.5, step=0.5, key="sld_duration")
    with pc2:
        sld_transition = st.number_input("Durata transizione (s)", value=float(default_tdur), min_value=0.0, step=0.1, key="sld_transition")
    with pc3:
        sld_resolution = st.selectbox("Risoluzione", res_labels, key="sld_resolution")
    with pc4:
        sld_fps = st.number_input("FPS", value=30, min_value=15, max_value=60, step=1, key="sld_fps")

    sld_fit = st.radio(
        "Adattamento foto",
        ["contain", "cover"],
        horizontal=True,
        format_func=lambda x: "Contieni (barre nere)" if x == "contain" else "Riempi (ritaglio)",
        key="sld_fit",
    )
    sld_output = st.text_input(
        "File video di output",
        value=str(library.EDITED_VIDEOS / "slideshow_v1.mp4"),
        key="sld_output",
    )

    if st.button("🎬 Crea slideshow professionale", key="sld_run", use_container_width=True):
        paths = [name_to_path[n] for n in sld_selected_names if n in name_to_path]
        paths = library.resolve_media_paths(paths, "photos")
        if len(paths) < 1:
            st.error("Seleziona almeno una foto dalla libreria (o caricane prima).")
        else:
            bad = []
            for p in paths:
                try:
                    from PIL import Image as _PILImage
                    with _PILImage.open(p) as im:
                        im.load()
                except Exception as e:
                    bad.append(f"{Path(p).name}: {e}")
            if bad:
                st.error("Impossibile aprire queste foto:\n- " + "\n- ".join(bad))
            else:
                music_path = library.resolve_media_path(sld_music, "music") if sld_music else None
                style_label = sld_template if sld_template != "Personalizzato" else "Personalizzato"
                with st.spinner(
                    f"Creazione stile {style_label} con {len(paths)} foto"
                    + (" + musica" if music_path else "")
                    + "..."
                ):
                    try:
                        out_path = library.next_version(sld_output)
                        video_slideshow.make_slideshow(
                            paths,
                            out_path,
                            duration=sld_duration,
                            transition=sld_transition,
                            resolution=sld_resolution,
                            fps=int(sld_fps),
                            music=music_path,
                            transition_type=sld_trans_type,
                            filter_name=sld_filter,
                            ken_burns=sld_ken_burns,
                            title=sld_title or None,
                            subtitle=sld_subtitle or None,
                            title_position=sld_title_pos,
                            music_volume=sld_music_vol,
                            fade_audio=sld_fade_audio,
                            fit=sld_fit,
                        )
                        st.success(f"✅ Slideshow creato ({style_label}): {out_path}")
                        if music_path:
                            st.caption(f"🎵 Musica: {Path(music_path).name} · volume {sld_music_vol}")
                        st.video(out_path)
                        _log("slideshow", f"{style_label} · {len(paths)} foto", out_path, "ok")
                        _refresh_library()
                    except Exception as e:
                        st.error(f"Errore slideshow: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# 🔗 TAB 4 — UNISCI VIDEO
# ═══════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("## 🔗 Unisci Video")
    st.markdown("Concatena più clip normalizzando risoluzione e framerate.")
    c1, c2 = st.columns(2)
    with c1:
        mrg_input = _folder_or_uploads(
            "video", "mrg_input",
            accept=["mp4", "mov", "avi", "mkv"],
            kind="videos", library_key="library_videos",
        )
    with c2:
        mrg_output = st.text_input("File video unito", value=str(library.EDITED_VIDEOS / "merged_v1.mp4"), key="mrg_output")
    c3, c4 = st.columns(2)
    with c3:
        mrg_resolution = st.selectbox("Risoluzione", ["1920x1080", "1280x720", "3840x2160"], key="mrg_resolution")
    with c4:
        mrg_fps = st.number_input("FPS", value=30, min_value=1, step=1, key="mrg_fps")
    if st.button("🔗 Unisci video", key="mrg_run"):
        p = Path(mrg_input.strip()) if mrg_input else Path("")
        if p.is_dir():
            paths = _list_files(mrg_input, VIDEO_EXTS)
        else:
            paths = [x.strip() for x in mrg_input.split(",") if x.strip()] if mrg_input else []
        if not paths:
            st.error("Nessun video trovato")
        else:
            with st.spinner("Unione video..."):
                try:
                    out_path = library.next_version(mrg_output)
                    video_merger.merge_videos(paths, out_path, mrg_resolution, mrg_fps)
                    st.success(f"Video unito: {out_path}")
                    st.video(out_path)
                    _log("merge", mrg_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════
# 🤖 TAB 5 — AI STUDIO
# ═══════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("## 🤖 AI Studio — OpenAI Integrata")
    if not ai_tools.is_configured():
        st.warning(
            "⚠️ **OpenAI non configurata.** Inserisci la tua `OPENAI_API_KEY` nel file `.env` "
            "per attivare le funzionalità AI (generazione immagini, analisi foto, assistente)."
        )
        st.code("OPENAI_API_KEY=sk-la-tua-chiave-qui", language="bash")
    else:
        st.success("✅ OpenAI configurata e pronta all'uso")

    ai_op = st.selectbox(
        "🎯 Funzione AI",
        [
            "🎨 Genera Immagine (DALL-E 3)",
            "🔍 Analizza Foto (GPT-4o Vision)",
            "💡 Suggerisci Miglioramenti",
            "📱 Genera Didascalia",
            "🔄 Crea Variazione",
            "💬 Assistente AI Foto/Video",
        ],
        key="ai_op",
    )

    if ai_op == "🎨 Genera Immagine (DALL-E 3)":
        st.markdown("### 🎨 Genera Immagine con DALL-E 3")
        ai_prompt = st.text_area(
            "Descrivi l'immagine che vuoi generare (in italiano o inglese)",
            placeholder="Es: Un paesaggio montano al tramonto con un lago cristallino in primo piano, stile fotorealistico",
            key="ai_gen_prompt",
        )
        ag1, ag2, ag3 = st.columns(3)
        with ag1:
            ai_size = st.selectbox("Dimensione", ["1024x1024", "1792x1024", "1024x1792"], key="ai_size")
        with ag2:
            ai_quality = st.selectbox("Qualità", ["hd", "standard"], key="ai_quality")
        with ag3:
            ai_style = st.selectbox("Stile", ["natural", "vivid"], key="ai_style")
        if st.button("🎨 Genera immagine", key="ai_gen_btn"):
            if not ai_prompt:
                st.error("Inserisci una descrizione")
            else:
                with st.spinner("🎨 Generazione con DALL-E 3 in corso..."):
                    try:
                        urls = ai_tools.generate_image(ai_prompt, ai_size, ai_quality, ai_style)
                        for i, url in enumerate(urls):
                            st.image(url, caption=f"Immagine generata {i+1}", use_container_width=True)
                            save_path = str(library.EDITED_PHOTOS / f"ai_generated_{i}.png")
                            save_path = library.next_version(save_path)
                            ai_tools.download_image(url, save_path)
                            st.success(f"Salvata in: {save_path}")
                            _log("ai_generate", ai_prompt[:100], save_path, "ok")
                    except Exception as e:
                        st.error(f"Errore: {e}")

    elif ai_op == "🔍 Analizza Foto (GPT-4o Vision)":
        st.markdown("### 🔍 Analisi Foto con GPT-4o Vision")
        ai_img = _file_or_upload(
            "foto da analizzare", "ai_analyze",
            accept=["jpg", "jpeg", "png", "webp"],
            kind="photos", library_key="library_images",
        )
        ai_custom_prompt = st.text_area(
            "Domanda personalizzata (opzionale)",
            value="Descrivi questa immagine in dettaglio in italiano.",
            key="ai_analyze_prompt",
        )
        if st.button("🔍 Analizza", key="ai_analyze_btn"):
            if not ai_img:
                st.error("Seleziona una foto")
            else:
                with st.spinner("🔍 Analisi con GPT-4o Vision..."):
                    try:
                        result = ai_tools.analyze_image(ai_img, ai_custom_prompt)
                        col_ai1, col_ai2 = st.columns([1, 2])
                        with col_ai1:
                            st.image(ai_img, use_container_width=True)
                        with col_ai2:
                            st.markdown(result)
                        _log("ai_analyze", ai_img, "", "ok")
                    except Exception as e:
                        st.error(f"Errore: {e}")

    elif ai_op == "💡 Suggerisci Miglioramenti":
        st.markdown("### 💡 Suggerimenti di Miglioramento AI")
        ai_img2 = _file_or_upload(
            "foto", "ai_suggest",
            accept=["jpg", "jpeg", "png", "webp"],
            kind="photos", library_key="library_images",
        )
        if st.button("💡 Ottieni suggerimenti", key="ai_suggest_btn"):
            if not ai_img2:
                st.error("Seleziona una foto")
            else:
                with st.spinner("💡 Analisi e suggerimenti..."):
                    try:
                        suggestions = ai_tools.suggest_edits(ai_img2)
                        st.image(ai_img2, width=400)
                        st.markdown("### 📋 Suggerimenti professionali:")
                        st.markdown(suggestions)
                        _log("ai_suggest", ai_img2, "", "ok")
                    except Exception as e:
                        st.error(f"Errore: {e}")

    elif ai_op == "📱 Genera Didascalia":
        st.markdown("### 📱 Genera Didascalia")
        ai_img3 = _file_or_upload(
            "foto", "ai_caption",
            accept=["jpg", "jpeg", "png", "webp"],
            kind="photos", library_key="library_images",
        )
        caption_style = st.selectbox(
            "Stile didascalia",
            ["social", "professionale", "poetica", "giornalistica", "e-commerce"],
            key="caption_style",
        )
        if st.button("📱 Genera didascalia", key="ai_caption_btn"):
            if not ai_img3:
                st.error("Seleziona una foto")
            else:
                with st.spinner("📱 Generazione didascalia..."):
                    try:
                        caption = ai_tools.generate_caption(ai_img3, caption_style)
                        st.image(ai_img3, width=400)
                        st.markdown("### 📝 Didascalia generata:")
                        st.markdown(caption)
                        _log("ai_caption", ai_img3, "", "ok")
                    except Exception as e:
                        st.error(f"Errore: {e}")

    elif ai_op == "🔄 Crea Variazione":
        st.markdown("### 🔄 Crea Variazioni con DALL-E 2")
        st.info("Genera variazioni creative basate su una foto esistente (richiede immagine PNG quadrata ≤ 4MB).")
        ai_img4 = _file_or_upload(
            "foto base", "ai_variation",
            accept=["png"],
            kind="photos", library_key="library_images",
        )
        var_n = st.number_input("Numero variazioni", value=1, min_value=1, max_value=4, key="var_n")
        if st.button("🔄 Genera variazioni", key="ai_var_btn"):
            if not ai_img4:
                st.error("Seleziona un'immagine PNG")
            else:
                with st.spinner("🔄 Generazione variazioni..."):
                    try:
                        urls = ai_tools.create_variation(ai_img4, var_n)
                        cols = st.columns(len(urls))
                        for i, (url, col) in enumerate(zip(urls, cols)):
                            with col:
                                st.image(url, caption=f"Variazione {i+1}", use_container_width=True)
                                save_path = library.next_version(str(library.EDITED_PHOTOS / f"variation_{i}.png"))
                                ai_tools.download_image(url, save_path)
                                st.caption(f"Salvata: {Path(save_path).name}")
                        _log("ai_variation", ai_img4, "", "ok")
                    except Exception as e:
                        st.error(f"Errore: {e}")

    elif ai_op == "💬 Assistente AI Foto/Video":
        st.markdown("### 💬 Assistente AI Esperto di Foto & Video")
        st.markdown(
            "Chiedi consigli su fotografia, ritocco, montaggio video, "
            "tecniche professionali, impostazioni della fotocamera e altro."
        )
        if "ai_chat_history" not in st.session_state:
            st.session_state.ai_chat_history = []

        for msg in st.session_state.ai_chat_history:
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            st.markdown(f"**{role_icon} {msg['role'].title()}:** {msg['content']}")

        ai_msg = st.text_area("Il tuo messaggio", key="ai_chat_msg", placeholder="Es: Come posso migliorare le mie foto di ritratto?")
        if st.button("💬 Invia", key="ai_chat_send"):
            if ai_msg:
                with st.spinner("🤖 Risposta in arrivo..."):
                    try:
                        response = ai_tools.ai_chat(ai_msg)
                        st.session_state.ai_chat_history.append({"role": "user", "content": ai_msg})
                        st.session_state.ai_chat_history.append({"role": "assistente", "content": response})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {e}")

        if st.button("🗑️ Cancella conversazione", key="ai_chat_clear"):
            st.session_state.ai_chat_history = []
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# 🔍 TAB 6 — DUPLICATI
# ═══════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown("## 🔍 Rilevamento Foto Duplicate")
    st.markdown("Trova foto duplicate o quasi identiche tramite hashing percettivo.")
    dup_folder = _folder_or_uploads(
        "foto", "dup_folder",
        accept=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
        kind="photos", library_key="library_images",
    )
    dup_threshold = st.slider("Soglia distanza Hamming", 0, 20, 10, key="dup_threshold")
    if st.button("🔍 Cerca duplicati", key="dup_search"):
        if not dup_folder or not Path(dup_folder).is_dir():
            st.error("Inserisci una cartella valida")
        else:
            with st.spinner("Scansione..."):
                try:
                    report = duplicate_finder.find_and_report(dup_folder, dup_threshold, False, None)
                    st.success(f"Trovati {report['duplicate_groups']} gruppi di duplicati su {report['total_images']} immagini")
                    _log("duplicates", dup_folder, "", "ok")
                    for i, group in enumerate(report["groups"], 1):
                        st.subheader(f"Gruppo {i} — migliore: {Path(group['best']).name}")
                        table = {"file": [], "risoluzione": []}
                        for f in group["duplicates"]:
                            table["file"].append(f)
                            table["risoluzione"].append(duplicate_finder._image_resolution(Path(f)))
                        st.table(table)
                    if report["duplicate_groups"] > 0:
                        if st.button("🗑️ Elimina copie a risoluzione minore", key="dup_delete"):
                            with st.spinner("Eliminazione..."):
                                try:
                                    duplicate_finder.find_and_report(dup_folder, dup_threshold, True, None)
                                    st.success("Copie eliminate.")
                                    _log("duplicates_delete", dup_folder, "", "ok")
                                except Exception as e:
                                    st.error(str(e))
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════
# ✨ TAB 7 — MIGLIORA FOTO
# ═══════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.markdown("## ✨ Migliora Foto Automaticamente")
    st.markdown("Correggi esposizione, contrasto e nitidezza delle immagini.")
    c1, c2 = st.columns(2)
    with c1:
        enh_in = _folder_or_uploads(
            "foto", "enh_in",
            accept=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
            kind="photos", library_key="library_images",
        )
        enh_batch = st.multiselect("Oppure seleziona foto (batch)", st.session_state.get("library_images", []), key="enh_batch")
    with c2:
        enh_out = st.text_input("Cartella uscita", value=str(library.EDITED_PHOTOS), key="enh_out")
    c3, c4, c5 = st.columns(3)
    with c3:
        gamma = st.number_input("Gamma", value=1.2, step=0.1, min_value=0.1, key="enh_gamma")
    with c4:
        sharp = st.number_input("Nitidezza", value=1.0, step=0.1, min_value=0.0, key="enh_sharp")
    with c5:
        blur = st.number_input("Soglia sfocatura", value=100.0, step=10.0, min_value=0.0, key="enh_blur")
    if st.button("✨ Migliora foto", key="enh_run"):
        targets = enh_batch if enh_batch else ([enh_in] if enh_in and Path(enh_in).is_dir() else [])
        if not targets or not enh_out:
            st.error("Inserisci una cartella o seleziona foto e la cartella di uscita")
        else:
            with st.spinner("Elaborazione..."):
                try:
                    if enh_batch:
                        photo_enhancer.enhance_files(enh_batch, enh_out, gamma, sharp, blur)
                    else:
                        photo_enhancer.enhance_folder(enh_in, enh_out, gamma, sharp, blur)
                    st.success(f"Foto migliorate salvate in: {enh_out}")
                    _log("enhance", str(targets), enh_out, "ok")
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════
# 👤 TAB 8 — FACE SWAP
# ═══════════════════════════════════════════════════════════════════════════
with tabs[8]:
    st.markdown("## 👤 Face Swap")
    st.markdown("Scambia il volto sorgente con quello in una foto destinazione.")
    st.warning("Il risultato include un watermark ed è destinato a scopi leciti e creativi.")
    c1, c2 = st.columns(2)
    with c1:
        face_src = _file_or_upload("foto sorgente", "face_src", accept=["jpg", "jpeg", "png", "webp"], kind="photos", library_key="library_images")
    with c2:
        face_dst = _file_or_upload("foto destinazione", "face_dst", accept=["jpg", "jpeg", "png", "webp"], kind="photos", library_key="library_images")
    face_out = st.text_input("Foto di output", value=str(library.EDITED_PHOTOS / "face_swap_v1.jpg"), key="face_out")
    consent = st.checkbox("Confermo di avere i diritti e il consenso per entrambe le immagini", key="face_consent")
    if st.button("👤 Scambia volto", key="face_run"):
        if not consent:
            st.error("Devi confermare i diritti e il consenso.")
        elif not face_src or not face_dst or not face_out:
            st.error("Inserisci tutti i percorsi")
        else:
            with st.spinner("Scambio volto..."):
                try:
                    out_path = library.next_version(face_out)
                    face_swap.swap_face(face_src, face_dst, out_path)
                    st.image(photo_editor.load_image(out_path), caption="Risultato", use_container_width=True)
                    st.success(f"Foto salvata: {out_path}")
                    _log("face_swap", f"{face_src} -> {face_dst}", out_path, "ok")
                    _refresh_library()
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════
# 🎵 TAB 9 — MUSICA
# ═══════════════════════════════════════════════════════════════════════════
with tabs[9]:
    st.markdown("## 🎵 Libreria Musica")
    st.markdown("Carica e gestisci tracce audio per slideshow e video.")
    uploaded_music = st.file_uploader(
        "Carica musica", accept_multiple_files=True,
        type=["mp3", "wav", "aac", "flac", "ogg", "m4a"], key="music_tab_uploader",
    )
    if uploaded_music:
        for up in uploaded_music:
            _save_upload(up, "music")
        _refresh_library()
    m_list = library.list_music()
    if m_list:
        for m in m_list:
            st.audio(m)
            st.caption(Path(m).name)
    else:
        st.info("Nessun brano caricato.")


# ═══════════════════════════════════════════════════════════════════════════
# 📁 TAB 10 — LAVORI SALVATI
# ═══════════════════════════════════════════════════════════════════════════
with tabs[10]:
    st.markdown("## 📁 Lavori Salvati")
    st.markdown("Foto e video modificati, pronti per download.")
    edited_photos = library.list_edited("photos")
    edited_videos = library.list_edited("videos")
    if edited_photos:
        st.subheader(f"📸 Foto modificate ({len(edited_photos)})")
        for i in range(0, len(edited_photos), 4):
            cols = st.columns(4)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(edited_photos):
                    with col:
                        try:
                            st.image(edited_photos[idx], use_container_width=True)
                        except Exception:
                            st.write(Path(edited_photos[idx]).name)
                        st.caption(Path(edited_photos[idx]).name)
                        with open(edited_photos[idx], "rb") as f:
                            st.download_button("⬇️ Scarica", f, file_name=Path(edited_photos[idx]).name, key=f"dl_img_{idx}")
    if edited_videos:
        st.subheader(f"🎥 Video prodotti ({len(edited_videos)})")
        for v in edited_videos:
            st.video(v)
            st.caption(Path(v).name)
            with open(v, "rb") as f:
                st.download_button("⬇️ Scarica", f, file_name=Path(v).name, key=f"dl_vid_{v}")
    if not edited_photos and not edited_videos:
        st.info("Nessun lavoro salvato. Modifica foto o video per vederli qui.")


# ═══════════════════════════════════════════════════════════════════════════
# 📊 TAB 11 — RIEPILOGO
# ═══════════════════════════════════════════════════════════════════════════
with tabs[11]:
    st.markdown("## 📊 Riepilogo")
    imgs, vids, music_files = _refresh_library()
    edited_p = library.list_edited("photos")
    edited_v = library.list_edited("videos")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📸 Foto originali", len(imgs))
    c2.metric("🎥 Video originali", len(vids))
    c3.metric("✏️ Foto modificate", len(edited_p))
    c4.metric("🎞️ Video prodotti", len(edited_v))
    total_sz = sum(f.stat().st_size for f in library.BASE.rglob("*") if f.is_file())
    st.metric("💾 Spazio occupato", f"{total_sz / (1024 * 1024):.1f} MB")
    user_id = auth.current_user_id()
    if user_id:
        jobs = db.list_jobs(user_id)[:10]
        if jobs:
            st.markdown("### 📋 Ultimi lavori")
            for j in jobs:
                st.write(f"🔹 **{j[1]}** — {str(j[2])[:60]} — _{j[4]}_")


# ═══════════════════════════════════════════════════════════════════════════
# 🎨 TAB 12 — PHOTOPEA
# ═══════════════════════════════════════════════════════════════════════════
with tabs[12]:
    st.markdown("## 🎨 Photopea — Editor Professionale Integrato")
    st.markdown(
        "Editor di immagini completo integrato nel browser. "
        "Supporta PSD, XCF, Sketch, AI, RAW e molti altri formati."
    )
    st.info("💡 Per usare Photopea: File → Apri → modifica → File → Esporta come → PNG/JPG → ricarica nella Libreria")
    st.components.v1.iframe("https://www.photopea.com", width=None, height=800, scrolling=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⚙️ TAB 13 — ADMIN
# ═══════════════════════════════════════════════════════════════════════════
with tabs[13]:
    st.markdown("## ⚙️ Gestione Utenti")
    if not auth.current_user_is_admin():
        st.error("Accesso riservato agli admin.")
    else:
        st.markdown("Crea nuovi utenti o gestisci quelli esistenti.")
        with st.form("create_user"):
            st.markdown("### ➕ Crea nuovo utente")
            new_username = st.text_input("Username", key="admin_new_user")
            new_password = st.text_input("Password", type="password", key="admin_new_pwd")
            is_admin_new = st.checkbox("Admin", key="admin_is_admin")
            create_btn = st.form_submit_button("Crea utente")
        if create_btn:
            if not new_username or not new_password:
                st.error("Inserisci username e password.")
            elif db.user_exists(new_username):
                st.error("Username già esistente.")
            else:
                if db.create_user(new_username, new_password, is_admin_new):
                    st.success(f"Utente {new_username} creato.")
                else:
                    st.error("Errore nella creazione.")

        users = db.list_users()
        if users:
            st.markdown("### 👥 Utenti esistenti")
            u_data = {"id": [], "username": [], "admin": [], "creato": []}
            for u in users:
                u_data["id"].append(u[0])
                u_data["username"].append(u[1])
                u_data["admin"].append("✅" if u[2] else "❌")
                u_data["creato"].append(u[3])
            st.dataframe(u_data)
            to_delete = st.number_input("ID utente da eliminare", min_value=0, step=1, key="admin_del_id")
            if st.button("🗑️ Elimina utente", key="admin_del_btn"):
                current = auth.current_user_id()
                if to_delete == current:
                    st.error("Non puoi eliminare te stesso.")
                elif db.delete_user(to_delete):
                    st.success(f"Utente {to_delete} eliminato.")
                else:
                    st.error("Errore nell'eliminazione.")


# ═══════════════════════════════════════════════════════════════════════════
# 📜 TAB 14 — STORICO
# ═══════════════════════════════════════════════════════════════════════════
with tabs[14]:
    st.markdown("## 📜 Storico Lavori")
    user_id = auth.current_user_id()
    if auth.current_user_is_admin():
        show_all = st.checkbox("Mostra tutti gli utenti", key="show_all_jobs")
        jobs = db.list_jobs() if show_all else db.list_jobs(user_id)
    else:
        jobs = db.list_jobs(user_id)
    if not jobs:
        st.info("Nessun lavoro trovato.")
    else:
        cols = ["id", "utente", "tipo", "input", "output", "stato", "data"]
        if not auth.current_user_is_admin():
            cols = [c for c in cols if c != "utente"]
        data = {c: [] for c in cols}
        for row in jobs:
            if auth.current_user_is_admin() and show_all:
                data["id"].append(row[0])
                data["utente"].append(row[1])
                data["tipo"].append(row[2])
                data["input"].append(row[3])
                data["output"].append(row[4])
                data["stato"].append(row[5])
                data["data"].append(row[6])
            else:
                data["id"].append(row[0])
                data["tipo"].append(row[1])
                data["input"].append(row[2])
                data["output"].append(row[3])
                data["stato"].append(row[4])
                data["data"].append(row[5])
        st.dataframe(data, use_container_width=True)

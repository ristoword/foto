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
import ai_utils as ai

library.init_library()


def _log(job_type, input_summary, output_path, status="ok"):
    user_id = auth.current_user_id()
    if user_id:
        db.log_job(user_id, job_type, input_summary, output_path, status)


st.set_page_config(page_title="AppFoto Studio", layout="wide")
auth.require_login()

st.markdown("""
<style>
    :root {
        --accent: #00f2ff;
        --accent-dark: #00b8c4;
        --bg: #0a0a0a;
        --surface: #121212;
        --surface-2: #1a1a1a;
        --border: #2a2a2a;
        --text: #f1f1f1;
        --muted: #a0a0a0;
    }
    .stApp {
        background-color: var(--bg);
        color: var(--text);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3 {
        color: var(--accent);
        font-weight: 600;
    }
    .main-header {
        text-align: center;
        margin-top: -1rem;
        margin-bottom: 0.2rem;
    }
    .main-header h1 {
        font-size: 4rem;
        font-weight: 800;
        color: var(--text);
        letter-spacing: -2px;
        text-transform: uppercase;
        text-shadow: 0 0 20px rgba(0, 242, 255, 0.4);
    }
    .sub-header {
        text-align: center;
        color: var(--muted);
        margin-bottom: 2rem;
        font-size: 0.95rem;
        font-weight: 500;
        letter-spacing: 0.35em;
        text-transform: uppercase;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--surface);
        padding: 0.6rem 1rem 0 1rem;
        border-radius: 14px 14px 0 0;
        border-bottom: 2px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: var(--surface-2);
        color: var(--muted);
        border-radius: 10px 10px 0 0;
        padding: 12px 24px;
        font-weight: 600;
        border: 1px solid var(--border);
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--accent);
        color: #0a0a0a;
        border-color: var(--accent);
        box-shadow: 0 -4px 12px rgba(0, 242, 255, 0.25);
    }
    div.stButton > button:first-child {
        background-color: var(--accent);
        color: #0a0a0a;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 1.4rem;
        font-weight: 700;
        transition: 0.2s;
        box-shadow: 0 4px 14px rgba(0, 242, 255, 0.25);
    }
    div.stButton > button:hover {
        background-color: var(--accent-dark);
        color: #0a0a0a;
        box-shadow: 0 6px 18px rgba(0, 242, 255, 0.35);
    }
    div.stButton > button:active {
        background-color: #00939c;
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stSlider"] label,
    div[data-testid="stSelectbox"] label {
        color: var(--text) !important;
        font-weight: 500;
    }
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stSelectbox"] > div > div {
        background-color: var(--surface-2) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
    }
    div[data-testid="stSlider"] > div > div > div,
    div[data-testid="stSlider"] [role="slider"] {
        color: var(--accent) !important;
    }
    div[data-baseweb="select"] > div {
        background-color: var(--surface-2) !important;
        border-color: var(--border) !important;
    }
    .stMarkdown, .stInfo, .stSuccess, .stError, .stWarning {
        color: var(--text);
    }
    .stInfo {
        background-color: var(--surface-2);
        border-left: 4px solid var(--accent);
    }
    .stSuccess {
        background-color: #0f2f1a;
        border-left: 4px solid #34d399;
    }
    .stError {
        background-color: #2f1010;
        border-left: 4px solid #f87171;
    }
    .stSidebar {
        background-color: var(--surface) !important;
        border-right: 1px solid var(--border);
    }
    .stSidebar [data-testid="stMetric"] {
        background-color: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.5rem;
    }
    .css-1c2njp7, .css-1d0tav8 { /* metric value */
        color: var(--accent) !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>AppFoto Studio</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Gestione foto e video professionale in un clic</div>', unsafe_allow_html=True)

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}
IMAGE_EXTS = library.IMAGE_EXTS
VIDEO_EXTS = library.VIDEO_EXTS
MUSIC_EXTS = library.MUSIC_EXTS


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


with st.sidebar:
    st.header("AppFoto Studio")
    st.markdown("""
    **Funzionalità:**
    - Rilevamento duplicati foto
    - Miglioramento automatico foto
    - Montaggio slideshow
    - Unione video
    - Editor video (taglio, filtri, audio, frame)
    """)
    st.info("Carica foto e video nella libreria qui sotto. Saranno disponibili in tutta l'app.")

    st.subheader("📁 Libreria")
    img_uploads = st.file_uploader("Carica foto", accept_multiple_files=True, type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"], key="lib_img_uploader")
    if img_uploads:
        paths = _save_uploads(img_uploads, "photos")
        for p in paths:
            db.log_upload(auth.current_user_id(), Path(p).name, p)
    vid_uploads = st.file_uploader("Carica video", accept_multiple_files=True, type=["mp4", "mov", "avi", "mkv"], key="lib_vid_uploader")
    if vid_uploads:
        paths = _save_uploads(vid_uploads, "videos")
        for p in paths:
            db.log_upload(auth.current_user_id(), Path(p).name, p)
    music_uploads = st.file_uploader("Carica musica", accept_multiple_files=True, type=["mp3", "wav", "aac", "flac", "ogg", "m4a"], key="lib_music_uploader")
    if music_uploads:
        paths = _save_uploads(music_uploads, "music")
        for p in paths:
            db.log_upload(auth.current_user_id(), Path(p).name, p)

    imgs, vids, music = _refresh_library()
    c1, c2, c3 = st.columns(3)
    c1.metric("Foto", len(imgs))
    c2.metric("Video", len(vids))
    c3.metric("Musica", len(music))
    if imgs:
        for i in range(0, min(len(imgs), 6), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(imgs):
                    with col:
                        try:
                            st.image(imgs[i + j], use_container_width=True)
                        except Exception:
                            st.write(Path(imgs[i + j]).name)
    if vids:
        st.markdown(f"**{len(vids)} video**")
        for v in vids:
            st.write(Path(v).name)
    if music:
        st.markdown(f"**{len(music)} brani**")
        for m in music:
            st.write(Path(m).name)

    # ── AI Assistente ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("🤖 Assistente AI")
    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    chat_box = st.container(height=220)
    with chat_box:
        for _msg in st.session_state.ai_chat_history[-8:]:
            _lbl = "👤 Tu" if _msg["role"] == "user" else "🤖 AI"
            st.markdown(f"**{_lbl}:** {_msg['content']}")

    _user_q = st.text_input(
        "Chiedi...", key="ai_sidebar_input",
        label_visibility="collapsed",
        placeholder="Es: Come miglioro le foto scure?",
    )
    _sb_col1, _sb_col2 = st.columns([3, 1])
    with _sb_col1:
        if st.button("Invia", key="ai_sidebar_send") and _user_q:
            st.session_state.ai_chat_history.append({"role": "user", "content": _user_q})
            with st.spinner("AI..."):
                _reply = ai.chat(st.session_state.ai_chat_history)
            st.session_state.ai_chat_history.append({"role": "assistant", "content": _reply})
            st.rerun()
    with _sb_col2:
        if st.button("🗑", key="ai_sidebar_clear", help="Cancella chat"):
            st.session_state.ai_chat_history = []
            st.rerun()


def _image_picker(label, key, library_key):
    lib = st.session_state.get(library_key, [])
    if not lib:
        st.info("Nessun file nella libreria")
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
        p = Path(selected).name
        st.markdown(f"✅ Selezionato: **{p}**")
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
        uploaded = st.file_uploader(f"Carica {label} (multiplo)", accept_multiple_files=True, type=accept, key=f"upl_{key}")
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


tabs = st.tabs(["Duplicati", "Migliora foto", "Slideshow", "Unione video", "Editor Video", "Editor Foto", "Face Swap", "Storico", "Admin", "Musica", "Riepilogo", "Lavori", "Photopea"])

# ══════════════════════════════════════════════════════════════════════════════
# Tab 0 — Duplicati
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.header("Rilevamento foto duplicate")
    st.markdown("Trova foto duplicate o quasi identiche tramite hashing percettivo.")
    dup_folder = _folder_or_uploads("foto", "dup_folder", accept=["jpg", "jpeg", "png", "webp", "bmp", "tiff"], kind="photos", library_key="library_images")
    dup_threshold = st.slider("Soglia distanza Hamming", 0, 20, 10, key="dup_threshold")
    if st.button("Cerca duplicati", key="dup_search"):
        if not dup_folder or not Path(dup_folder).is_dir():
            st.error("Inserisci una cartella valida")
        else:
            with st.spinner("Scansione in corso..."):
                try:
                    report = duplicate_finder.find_and_report(dup_folder, dup_threshold, False, None)
                except Exception as e:
                    st.error(str(e))
                else:
                    st.success(f"Trovati {report['duplicate_groups']} gruppi di duplicati su {report['total_images']} immagini")
                    st.session_state["last_dup_report"] = report
                    _log("duplicates", dup_folder, "", "ok")
                    for i, group in enumerate(report['groups'], 1):
                        st.subheader(f"Gruppo {i} — migliore: {Path(group['best']).name}")
                        table = {"file": [], "risoluzione": []}
                        for f in group['duplicates']:
                            table['file'].append(f)
                            table['risoluzione'].append(duplicate_finder._image_resolution(Path(f)))
                        st.table(table)
                    if report['duplicate_groups'] > 0:
                        if st.button("Elimina tutte le copie a risoluzione minore", key="dup_delete"):
                            with st.spinner("Eliminazione in corso..."):
                                try:
                                    duplicate_finder.find_and_report(dup_folder, dup_threshold, True, None)
                                except Exception as e:
                                    st.error(str(e))
                                else:
                                    st.success("Copie duplicate eliminate. E rimasta solo quella con risoluzione maggiore per gruppo.")
                                    _log("duplicates_delete", dup_folder, "", "ok")

    # ── AI: Analisi duplicati ─────────────────────────────────────────────
    st.divider()
    with st.expander("🤖 AI: Analisi duplicati e consigli"):
        _n_lib = len(st.session_state.get("library_images", []))
        if st.button("💡 Consigli AI sulla gestione duplicati", key="ai_dup_advice_btn"):
            with st.spinner("AI analizza la tua libreria..."):
                _result = ai.ask(
                    f"Ho una libreria fotografica con {_n_lib} immagini. "
                    "Dammi 4 consigli pratici per prevenire e gestire le foto duplicate in modo efficiente."
                )
                st.session_state["ai_dup_advice"] = _result
        if "ai_dup_advice" in st.session_state:
            st.info(st.session_state["ai_dup_advice"])

        # Per-group AI analysis from the last search result
        _last_report = st.session_state.get("last_dup_report")
        if _last_report and _last_report.get("groups"):
            st.markdown("**Analisi AI per ogni gruppo trovato:**")
            for _gi, _grp in enumerate(_last_report["groups"], 1):
                _gcol1, _gcol2 = st.columns([4, 1])
                with _gcol1:
                    st.markdown(f"Gruppo {_gi}: `{Path(_grp['best']).name}`")
                with _gcol2:
                    if st.button("Analizza", key=f"ai_dup_grp_btn_{_gi}"):
                        with st.spinner(f"AI analizza gruppo {_gi}..."):
                            _grp_rec = ai.analyze_duplicate_group(_grp)
                            st.session_state[f"ai_dup_grp_{_gi}"] = _grp_rec
                if st.session_state.get(f"ai_dup_grp_{_gi}"):
                    st.caption(st.session_state[f"ai_dup_grp_{_gi}"])

# ══════════════════════════════════════════════════════════════════════════════
# Tab 1 — Migliora foto
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    # Apply pending AI enhance params before widgets render
    if st.session_state.pop("_apply_ai_enhance", False):
        _ep = st.session_state.get("_ai_enhance_params", {})
        if "gamma" in _ep:
            st.session_state["enh_gamma"] = float(_ep["gamma"])
        if "sharpness" in _ep:
            st.session_state["enh_sharp"] = float(_ep["sharpness"])

    st.header("Migliora foto")
    st.markdown("Correggi esposizione, contrasto e nitidezza delle immagini.")
    c1, c2 = st.columns(2)
    with c1:
        enh_in = _folder_or_uploads("foto", "enh_in", accept=["jpg", "jpeg", "png", "webp", "bmp", "tiff"], kind="photos", library_key="library_images")
        enh_batch = st.multiselect("Oppure seleziona foto (batch)", st.session_state.get("library_images", []), key="enh_batch")
    with c2:
        enh_out = st.text_input("Cartella foto in uscita", value=str(library.EDITED_PHOTOS), key="enh_out")
    c3, c4, c5 = st.columns(3)
    with c3:
        gamma = st.number_input("Gamma", value=1.2, step=0.1, min_value=0.1, key="enh_gamma")
    with c4:
        sharp = st.number_input("Nitidezza", value=1.0, step=0.1, min_value=0.0, key="enh_sharp")
    with c5:
        blur = st.number_input("Soglia sfocatura", value=100.0, step=10.0, min_value=0.0, key="enh_blur")
    if st.button("Migliora foto", key="enh_run"):
        targets = enh_batch if enh_batch else ([enh_in] if enh_in and Path(enh_in).is_dir() else [])
        if not targets or not enh_out:
            st.error("Inserisci una cartella o seleziona foto e la cartella di uscita")
        else:
            with st.spinner("Elaborazione in corso..."):
                try:
                    if enh_batch:
                        photo_enhancer.enhance_files(enh_batch, enh_out, gamma, sharp, blur)
                    else:
                        photo_enhancer.enhance_folder(enh_in, enh_out, gamma, sharp, blur)
                except Exception as e:
                    st.error(str(e))
                else:
                    st.success(f"Foto migliorate salvate in: {enh_out}")
                    _log("enhance", str(targets), enh_out, "ok")

    # ── AI: Suggerisci parametri ──────────────────────────────────────────
    st.divider()
    with st.expander("🤖 AI: Suggerisci parametri di miglioramento"):
        _enh_imgs = st.session_state.get("library_images", [])
        _enh_candidates = enh_batch if enh_batch else _enh_imgs
        if _enh_candidates:
            _enh_pick = st.selectbox(
                "Foto da analizzare con AI",
                _enh_candidates,
                format_func=lambda p: Path(p).name,
                key="ai_enh_pick",
            )
            if st.button("🔍 Analizza con AI e suggerisci parametri", key="ai_enh_analyze_btn"):
                if _enh_pick and Path(_enh_pick).is_file():
                    with st.spinner("AI analizza la foto..."):
                        _ep = ai.suggest_enhance_params(_enh_pick)
                        st.session_state["_ai_enhance_params"] = _ep
                else:
                    st.warning("File non trovato.")

            if "_ai_enhance_params" in st.session_state:
                _ep = st.session_state["_ai_enhance_params"]
                _ec1, _ec2 = st.columns(2)
                _ec1.metric("Gamma consigliato", f"{_ep.get('gamma', 1.2):.2f}")
                _ec2.metric("Nitidezza consigliata", f"{_ep.get('sharpness', 1.0):.2f}")
                if _ep.get("reason"):
                    st.info(f"💡 {_ep['reason']}")
                if st.button("✅ Applica parametri AI", key="ai_enh_apply_btn"):
                    st.session_state["_apply_ai_enhance"] = True
                    st.rerun()
        else:
            st.info("Carica o seleziona almeno una foto per usare l'analisi AI.")

# ══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Slideshow
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.header("Crea slideshow da foto")
    st.markdown("Genera un video con transizioni a dissolvenza a partire dalle tue foto.")
    c1, c2 = st.columns(2)
    with c1:
        sld_input = _folder_or_uploads("foto", "sld_input", accept=["jpg", "jpeg", "png", "webp", "bmp", "tiff"], kind="photos", library_key="library_images")
    with c2:
        sld_output = st.text_input("File video di output", value=str(library.EDITED_VIDEOS / "slideshow_v1.mp4"), key="sld_output")
    c3, c4, c5 = st.columns(3)
    with c3:
        sld_duration = st.number_input("Durata immagine (s)", value=3.0, min_value=0.1, step=0.5, key="sld_duration")
    with c4:
        sld_transition = st.number_input("Transizione (s)", value=0.5, min_value=0.0, step=0.1, key="sld_transition")
    with c5:
        sld_fps = st.number_input("FPS", value=30, min_value=1, step=1, key="sld_fps")
    c6, c7 = st.columns(2)
    with c6:
        sld_resolution = st.selectbox("Risoluzione", ["1920x1080", "1280x720", "3840x2160"], key="sld_resolution")
    with c7:
        sld_music = st.selectbox("Musica di sottofondo (opzionale)", [""] + library.list_music(), key="sld_music")
    if st.button("Crea slideshow", key="sld_run"):
        p = Path(sld_input.strip())
        if p.is_dir():
            paths = _list_files(sld_input, IMAGE_EXTS)
        else:
            paths = [x.strip() for x in sld_input.split(",") if x.strip()]
        if not paths:
            st.error("Nessuna immagine trovata")
        else:
            with st.spinner("Creazione video in corso... Questo puo richiedere tempo"):
                try:
                    out_path = library.next_version(sld_output)
                    video_slideshow.make_slideshow(paths, out_path, sld_duration, sld_transition, sld_resolution, sld_fps, sld_music or None)
                except Exception as e:
                    st.error(str(e))
                else:
                    st.success(f"Slideshow salvato in: {out_path}")
                    st.video(out_path)
                    _log("slideshow", sld_input, out_path, "ok")

    # ── AI: Genera metadati slideshow ─────────────────────────────────────
    st.divider()
    with st.expander("🤖 AI: Genera titolo, descrizione e durata ottimale"):
        if st.button("✨ Genera metadati AI per questo slideshow", key="ai_sld_meta_btn"):
            _sld_imgs = st.session_state.get("library_images", [])
            _sld_folder = Path(sld_input).name if sld_input else ""
            _sld_names = [Path(p).name for p in _sld_imgs[:8]]
            with st.spinner("AI genera metadati..."):
                _sld_meta = ai.generate_slideshow_metadata(
                    n_photos=len(_sld_imgs),
                    folder_name=_sld_folder,
                    photo_names=_sld_names,
                )
                st.session_state["ai_sld_meta"] = _sld_meta

        if "ai_sld_meta" in st.session_state:
            _m = st.session_state["ai_sld_meta"]
            st.markdown(f"**🎬 Titolo:** {_m['title']}")
            st.markdown(f"**📝 Descrizione:** {_m['description']}")
            st.metric("⏱ Durata consigliata per foto (s)", _m['duration'])
            if st.button("✅ Usa durata consigliata", key="ai_sld_apply_duration"):
                st.session_state["sld_duration"] = float(_m["duration"])
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# Tab 3 — Unione video
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.header("Unisci video")
    st.markdown("Concatena piu clip in un unico video normalizzando risoluzione e framerate.")
    c1, c2 = st.columns(2)
    with c1:
        mrg_input = _folder_or_uploads("video", "mrg_input", accept=["mp4", "mov", "avi", "mkv"], kind="videos", library_key="library_videos")
    with c2:
        mrg_output = st.text_input("File video unito", value=str(library.EDITED_VIDEOS / "merged_v1.mp4"), key="mrg_output")
    c3, c4 = st.columns(2)
    with c3:
        mrg_resolution = st.selectbox("Risoluzione", ["1920x1080", "1280x720", "3840x2160"], key="mrg_resolution")
    with c4:
        mrg_fps = st.number_input("FPS", value=30, min_value=1, step=1, key="mrg_fps")
    if st.button("Unisci video", key="mrg_run"):
        p = Path(mrg_input.strip())
        if p.is_dir():
            paths = _list_files(mrg_input, VIDEO_EXTS)
        else:
            paths = [x.strip() for x in mrg_input.split(",") if x.strip()]
        if not paths:
            st.error("Nessun video trovato")
        else:
            with st.spinner("Unione video in corso..."):
                try:
                    out_path = library.next_version(mrg_output)
                    video_merger.merge_videos(paths, out_path, mrg_resolution, mrg_fps)
                except Exception as e:
                    st.error(str(e))
                else:
                    st.success(f"Video unito salvato in: {out_path}")
                    st.video(out_path)
                    _log("merge", mrg_input, out_path, "ok")

    # ── AI: Struttura narrativa ───────────────────────────────────────────
    st.divider()
    with st.expander("🤖 AI: Struttura narrativa e ordine clip"):
        _mrg_vids = st.session_state.get("library_videos", [])
        _mrg_names = [Path(v).name for v in _mrg_vids]
        if st.button("🎬 Analizza struttura narrativa con AI", key="ai_mrg_order_btn"):
            with st.spinner("AI analizza i clip..."):
                _mrg_result = ai.suggest_merge_order(_mrg_names)
                st.session_state["ai_mrg_order"] = _mrg_result
        if "ai_mrg_order" in st.session_state:
            st.info(st.session_state["ai_mrg_order"])

# ══════════════════════════════════════════════════════════════════════════════
# Tab 4 — Editor Video
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.header("Editor Video")
    st.markdown("Taglia clip, aggiungi musica, applica filtri artistici ed estrai frame.")
    operation = st.selectbox("Operazione", ["Taglia", "Aggiungi musica", "Applica filtro", "Estrai frame"], key="vid_op")
    c1, c2 = st.columns(2)
    with c1:
        vid_input = _file_or_upload("video", "vid_input", accept=["mp4", "mov", "avi", "mkv"], kind="videos", library_key="library_videos")
    with c2:
        vid_output = st.text_input("File/cartella di uscita", value=str(library.EDITED_VIDEOS / "output_v1.mp4"), key="vid_output")
    if operation == "Taglia":
        c3, c4 = st.columns(2)
        with c3:
            start_t = st.number_input("Inizio (s)", value=0.0, min_value=0.0, step=0.1, key="vid_start")
        with c4:
            end_t = st.number_input("Fine (s)", value=10.0, min_value=0.0, step=0.1, key="vid_end")
        if st.button("Taglia video", key="vid_trim"):
            with st.spinner("Taglio in corso..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.trim_video(vid_input, out_path, start_t, end_t)
                    st.success(f"Video tagliato: {out_path}")
                    st.video(out_path)
                    _log("video_trim", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))
        # AI suggestion for trim
        with st.expander("🤖 AI: Consigli per il taglio"):
            if st.button("💡 Strategie di taglio AI", key="ai_vid_trim_btn"):
                _vname = Path(vid_input).name if vid_input else "video"
                with st.spinner("AI analizza..."):
                    st.session_state["ai_vid_trim"] = ai.suggest_trim_points(_vname)
            if "ai_vid_trim" in st.session_state:
                st.info(st.session_state["ai_vid_trim"])

    elif operation == "Aggiungi musica":
        audio_file = st.selectbox("File audio", [""] + library.list_music(), key="vid_audio")
        loop_audio = st.checkbox("Ripeti audio se piu corto del video", key="vid_loop")
        if st.button("Aggiungi musica", key="vid_music_btn"):
            with st.spinner("Aggiunta audio..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.add_music_to_video(vid_input, audio_file, out_path, loop_audio)
                    st.success(f"Audio aggiunto: {out_path}")
                    st.video(out_path)
                    _log("video_music", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))
        # AI suggestion for audio pairing
        with st.expander("🤖 AI: Abbinamento musicale"):
            if st.button("🎵 Suggerisci traccia AI", key="ai_vid_audio_btn"):
                _vname = Path(vid_input).name if vid_input else "video"
                _mnames = [Path(m).name for m in library.list_music()]
                with st.spinner("AI analizza..."):
                    st.session_state["ai_vid_audio"] = ai.suggest_audio_pairing(_vname, _mnames)
            if "ai_vid_audio" in st.session_state:
                st.info(st.session_state["ai_vid_audio"])

    elif operation == "Applica filtro":
        filter_name = st.selectbox("Filtro", ["grayscale", "blur", "negate", "edgedetect", "vignette", "sharpen"], key="vid_filter")
        if st.button("Applica filtro", key="vid_filter_btn"):
            with st.spinner("Applicazione filtro..."):
                try:
                    out_path = library.next_version(vid_output)
                    video_editor.apply_filter(vid_input, out_path, filter_name)
                    st.success(f"Filtro applicato: {out_path}")
                    st.video(out_path)
                    _log("video_filter", vid_input, out_path, "ok")
                except Exception as e:
                    st.error(str(e))
        # AI filter suggestion
        with st.expander("🤖 AI: Suggerisci filtro"):
            if st.button("🎨 Quale filtro usare?", key="ai_vid_filter_btn"):
                _vname = Path(vid_input).name if vid_input else "video"
                with st.spinner("AI analizza..."):
                    st.session_state["ai_vid_filter"] = ai.suggest_video_filter(_vname)
            if "ai_vid_filter" in st.session_state:
                st.info(st.session_state["ai_vid_filter"])

    elif operation == "Estrai frame":
        interval = st.number_input("Intervallo in secondi", value=1.0, min_value=0.1, step=0.1, key="vid_interval")
        if st.button("Estrai frame", key="vid_frames"):
            with st.spinner("Estrazione frame..."):
                try:
                    video_editor.extract_frames(vid_input, vid_output, interval)
                    st.success(f"Frame estratti in: {vid_output}")
                    _log("video_frames", vid_input, vid_output, "ok")
                except Exception as e:
                    st.error(str(e))
        # AI interval suggestion
        with st.expander("🤖 AI: Intervallo ottimale"):
            if st.button("⏱ Suggerisci intervallo AI", key="ai_vid_interval_btn"):
                _vname = Path(vid_input).name if vid_input else "video"
                with st.spinner("AI analizza..."):
                    st.session_state["ai_vid_interval"] = ai.suggest_frame_interval(_vname)
            if "ai_vid_interval" in st.session_state:
                st.info(st.session_state["ai_vid_interval"])

# ══════════════════════════════════════════════════════════════════════════════
# Tab 5 — Editor Foto
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    # Apply pending AI editor settings BEFORE any widget renders
    if st.session_state.pop("_apply_ai_edit", False):
        _ae = st.session_state.get("_ai_edit_settings", {})
        _clamp = lambda v, lo, hi: max(lo, min(hi, v))
        if "brightness" in _ae:
            st.session_state["edit_brightness"] = _clamp(float(_ae["brightness"]), 0.0, 3.0)
        if "contrast" in _ae:
            st.session_state["edit_contrast"] = _clamp(float(_ae["contrast"]), 0.0, 3.0)
        if "saturation" in _ae:
            st.session_state["edit_saturation"] = _clamp(float(_ae["saturation"]), 0.0, 3.0)
        if "sharpen" in _ae:
            st.session_state["edit_sharpen"] = _clamp(float(_ae["sharpen"]), 0.0, 2.0)
        if "filter" in _ae:
            st.session_state["edit_filter"] = _ae["filter"]

    st.header("Editor Foto")
    st.markdown("Ritaglia, ruota, ridimensiona e applica correzioni alle foto.")
    c1, c2 = st.columns(2)
    with c1:
        edit_input = _file_or_upload("foto", "edit_input", accept=["jpg", "jpeg", "png", "webp", "bmp", "tiff"], kind="photos", library_key="library_images")
    with c2:
        edit_default = ""
        if edit_input:
            p = Path(edit_input)
            edit_default = str(library.EXPORTS / f"{p.stem}_v1{p.suffix}")
        edit_output = st.text_input("Foto in uscita", value=edit_default, key="edit_output")
    placeholder = np.full((300, 400, 3), 40, dtype=np.uint8)
    if edit_input:
        p = Path(edit_input).resolve()
        if p.is_file():
            try:
                preview = photo_editor.load_image(str(p))
                st.image(preview, caption="Anteprima originale", use_container_width=True)
            except Exception as e:
                st.error(f"Impossibile caricare l'anteprima: {e}")
                st.image(placeholder, caption="Nessuna immagine valida", use_container_width=True)
        else:
            st.error(f"File non trovato: {edit_input}")
            st.image(placeholder, caption="Nessuna immagine valida", use_container_width=True)
    else:
        st.image(placeholder, caption="Seleziona o carica un'immagine", use_container_width=True)
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
        edit_brightness = st.slider("Luminosità", 0.0, 3.0, 1.0, 0.1, key="edit_brightness")
    with c8:
        edit_contrast = st.slider("Contrasto", 0.0, 3.0, 1.0, 0.1, key="edit_contrast")
    with c9:
        edit_saturation = st.slider("Saturazione", 0.0, 3.0, 1.0, 0.1, key="edit_saturation")
    with c10:
        edit_sharpen = st.slider("Nitidezza", 0.0, 2.0, 0.0, 0.1, key="edit_sharpen")
    c11, c12 = st.columns(2)
    with c11:
        edit_filter = st.selectbox("Filtro", ["nessuno", "grayscale", "sepia", "blur", "sharpen", "emboss", "edge", "contour"], key="edit_filter")
    with c12:
        edit_mirror_h = st.checkbox("Specchio orizzontale", key="edit_mirror_h")
        edit_mirror_v = st.checkbox("Specchio verticale", key="edit_mirror_v")

    with st.expander("Regolazioni avanzate"):
        st.markdown("Curve e bilanciamento colore")
        edit_curve_shadow = st.slider("Ombre", 0, 128, 0, key="edit_curve_shadow")
        edit_curve_highlight = st.slider("Luci", 128, 255, 255, key="edit_curve_highlight")
        st.markdown("Bilanciamento colore (RGB)")
        cb_shadow_r = st.slider("R ombre", -50, 50, 0, key="cb_sr")
        cb_shadow_g = st.slider("G ombre", -50, 50, 0, key="cb_sg")
        cb_shadow_b = st.slider("B ombre", -50, 50, 0, key="cb_sb")
        cb_mid_r = st.slider("R mezzitoni", -50, 50, 0, key="cb_mr")
        cb_mid_g = st.slider("G mezzitoni", -50, 50, 0, key="cb_mg")
        cb_mid_b = st.slider("B mezzitoni", -50, 50, 0, key="cb_mb")
        cb_high_r = st.slider("R luci", -50, 50, 0, key="cb_hr")
        cb_high_g = st.slider("G luci", -50, 50, 0, key="cb_hg")
        cb_high_b = st.slider("B luci", -50, 50, 0, key="cb_hb")
        st.markdown("HSL")
        edit_hue = st.slider("Tonalità", -180, 180, 0, key="edit_hue")
        edit_hsl_sat = st.slider("Saturazione HSL", 0.0, 2.0, 1.0, 0.1, key="edit_hsl_sat")
        edit_light = st.slider("Luminosità HSL", -0.5, 0.5, 0.0, 0.05, key="edit_light")
        edit_vibrance = st.slider("Vibranza", -1.0, 1.0, 0.0, 0.1, key="edit_vibrance")
        edit_vignette = st.slider("Vignettatura", 0.0, 1.0, 0.0, 0.05, key="edit_vignette")
        edit_duotone = st.checkbox("Duotono", key="edit_duotone")
        if edit_duotone:
            edit_dt1 = st.color_picker("Colore ombre", "#1a1a1a", key="edit_dt1")
            edit_dt2 = st.color_picker("Colore luci", "#f2c94c", key="edit_dt2")

    def _edit_kwargs():
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
        return kwargs

    c13, c14 = st.columns(2)
    with c13:
        preview = st.button("👁️ Anteprima", key="edit_preview")
    with c14:
        save = st.button("💾 Salva modifiche", key="edit_save")

    if preview:
        if not edit_input:
            st.error("Seleziona una foto")
        else:
            with st.spinner("Anteprima in corso..."):
                try:
                    preview_path = str(library.EDITED_PHOTOS / f"preview_{Path(edit_input).stem}.jpg")
                    photo_editor.process_image(edit_input, preview_path, **_edit_kwargs())
                    st.image(photo_editor.load_image(preview_path), caption="Anteprima modifiche", use_container_width=True)
                except Exception as e:
                    st.error(str(e))

    if save:
        if not edit_input or not edit_output:
            st.error("Inserisci foto in ingresso e in uscita")
        else:
            with st.spinner("Salvataggio in corso..."):
                try:
                    out_path = library.next_version(edit_output)
                    photo_editor.process_image(edit_input, out_path, **_edit_kwargs())
                    st.image(photo_editor.load_image(out_path), caption="Risultato salvato", use_container_width=True)
                    st.success(f"Foto salvata in: {out_path}")
                    _log("photo_edit", edit_input, out_path, "ok")
                    _refresh_library()
                except Exception as e:
                    st.error(str(e))

    # ── AI: Suggerisci impostazioni editor ────────────────────────────────
    st.divider()
    with st.expander("🤖 AI: Analizza foto e suggerisci impostazioni ottimali"):
        if edit_input and Path(edit_input).is_file():
            if st.button("🔍 Analizza con AI", key="ai_edit_analyze_btn"):
                with st.spinner("AI analizza la foto con visione artificiale..."):
                    _ae_settings = ai.suggest_edit_settings(edit_input)
                    st.session_state["_ai_edit_settings"] = _ae_settings

            if "_ai_edit_settings" in st.session_state:
                _ae = st.session_state["_ai_edit_settings"]
                st.markdown("**Impostazioni consigliate dall'AI:**")
                _ae_c1, _ae_c2, _ae_c3, _ae_c4 = st.columns(4)
                _ae_c1.metric("Luminosità", f"{_ae.get('brightness', 1.0):.2f}")
                _ae_c2.metric("Contrasto",  f"{_ae.get('contrast',   1.0):.2f}")
                _ae_c3.metric("Saturazione",f"{_ae.get('saturation', 1.0):.2f}")
                _ae_c4.metric("Nitidezza",  f"{_ae.get('sharpen',    0.0):.2f}")
                st.write(f"**Filtro consigliato:** `{_ae.get('filter', 'nessuno')}`")
                if _ae.get("reason"):
                    st.info(f"💡 {_ae['reason']}")
                if st.button("✅ Applica impostazioni AI agli slider", key="ai_edit_apply_btn"):
                    st.session_state["_apply_ai_edit"] = True
                    st.rerun()
        else:
            st.info("Seleziona o carica una foto nell'editor per analizzarla con AI.")

# ══════════════════════════════════════════════════════════════════════════════
# Tab 6 — Face Swap
# ══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.header("Face Swap")
    st.markdown("Scambia il volto sorgente con quello in una foto destinazione. Usa solo foto di tua proprietà e con consenso.")
    st.warning("Il risultato include un watermark 'GENERATED' ed è destinato a scopi leciti e creativi.")
    c1, c2 = st.columns(2)
    with c1:
        face_src = _file_or_upload("foto sorgente", "face_src", accept=["jpg", "jpeg", "png", "webp"], kind="photos", library_key="library_images")
    with c2:
        face_dst = _file_or_upload("foto destinazione", "face_dst", accept=["jpg", "jpeg", "png", "webp"], kind="photos", library_key="library_images")
    face_default = str(library.EDITED_PHOTOS / "face_swap_v1.jpg")
    face_out = st.text_input("Foto di output", value=face_default, key="face_out")
    consent = st.checkbox("Confermo di avere i diritti e il consenso per entrambe le immagini", key="face_consent")
    if st.button("Scambia volto", key="face_run"):
        if not consent:
            st.error("Devi confermare i diritti e il consenso per procedere.")
        elif not face_src or not face_dst or not face_out:
            st.error("Inserisci tutti i percorsi")
        else:
            with st.spinner("Scambio volto in corso..."):
                try:
                    out_path = library.next_version(face_out)
                    face_swap.swap_face(face_src, face_dst, out_path)
                    st.image(photo_editor.load_image(out_path), caption="Risultato", use_container_width=True)
                    st.success(f"Foto salvata in: {out_path}")
                    _log("face_swap", f"{face_src} -> {face_dst}", out_path, "ok")
                    _refresh_library()
                except Exception as e:
                    st.error(str(e))

    # ── AI: Analisi qualità per face swap ─────────────────────────────────
    st.divider()
    with st.expander("🤖 AI: Analisi qualità foto per face swap"):
        _fs_col1, _fs_col2 = st.columns(2)
        with _fs_col1:
            if face_src and Path(face_src).is_file():
                if st.button("🔍 Analizza foto sorgente", key="ai_face_src_btn"):
                    with st.spinner("AI analizza..."):
                        st.session_state["ai_face_src"] = ai.check_face_swap_quality(face_src)
                if "ai_face_src" in st.session_state:
                    st.markdown("**Sorgente:**")
                    st.info(st.session_state["ai_face_src"])
            else:
                st.caption("Carica la foto sorgente per l'analisi AI.")
        with _fs_col2:
            if face_dst and Path(face_dst).is_file():
                if st.button("🔍 Analizza foto destinazione", key="ai_face_dst_btn"):
                    with st.spinner("AI analizza..."):
                        st.session_state["ai_face_dst"] = ai.check_face_swap_quality(face_dst)
                if "ai_face_dst" in st.session_state:
                    st.markdown("**Destinazione:**")
                    st.info(st.session_state["ai_face_dst"])
            else:
                st.caption("Carica la foto destinazione per l'analisi AI.")

# ══════════════════════════════════════════════════════════════════════════════
# Tab 7 — Storico
# ══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.header("Storico")
    st.markdown("Storico dei lavori eseguiti.")
    user_id = auth.current_user_id()
    if auth.current_user_is_admin():
        show_all = st.checkbox("Mostra tutti gli utenti", key="show_all_jobs")
        jobs = db.list_jobs() if show_all else db.list_jobs(user_id)
    else:
        show_all = False
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
        st.dataframe(data)

    # ── AI: Riepilogo attività ─────────────────────────────────────────────
    st.divider()
    with st.expander("🤖 AI: Riepilogo intelligente attività"):
        if st.button("📊 Genera riepilogo AI", key="ai_jobs_summary_btn"):
            with st.spinner("AI analizza lo storico..."):
                _is_adm = auth.current_user_is_admin() and show_all
                st.session_state["ai_jobs_summary"] = ai.summarize_activity(jobs, is_admin=_is_adm)
        if "ai_jobs_summary" in st.session_state:
            st.info(st.session_state["ai_jobs_summary"])

# ══════════════════════════════════════════════════════════════════════════════
# Tab 8 — Admin
# ══════════════════════════════════════════════════════════════════════════════
with tabs[8]:
    st.header("Gestione utenti")
    if not auth.current_user_is_admin():
        st.error("Accesso riservato agli admin.")
    else:
        st.markdown("Crea nuovi utenti o visualizza/elimin quelli esistenti.")
        with st.form("create_user"):
            st.markdown("### Crea nuovo utente")
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
            st.markdown("### Utenti esistenti")
            u_data = {"id": [], "username": [], "admin": [], "creato": []}
            for u in users:
                u_data["id"].append(u[0])
                u_data["username"].append(u[1])
                u_data["admin"].append(u[2])
                u_data["creato"].append(u[3])
            st.dataframe(u_data)

            to_delete = st.number_input("ID utente da eliminare", min_value=0, step=1, key="admin_del_id")
            if st.button("Elimina utente", key="admin_del_btn"):
                current = auth.current_user_id()
                if to_delete == current:
                    st.error("Non puoi eliminare te stesso.")
                elif db.delete_user(to_delete):
                    st.success(f"Utente {to_delete} eliminato.")
                else:
                    st.error("Errore nell'eliminazione.")

        # ── AI: Report piattaforma ─────────────────────────────────────────
        st.divider()
        with st.expander("🤖 AI: Report piattaforma e analisi utenti"):
            if st.button("📈 Genera report AI", key="ai_admin_report_btn"):
                _all_jobs = db.list_jobs()
                with st.spinner("AI genera il report..."):
                    st.session_state["ai_admin_report"] = ai.analyze_admin_activity(
                        users=users,
                        total_jobs=len(_all_jobs),
                    )
            if "ai_admin_report" in st.session_state:
                st.info(st.session_state["ai_admin_report"])

# ══════════════════════════════════════════════════════════════════════════════
# Tab 9 — Musica
# ══════════════════════════════════════════════════════════════════════════════
with tabs[9]:
    st.header("Libreria musica")
    st.markdown("Carica e gestisci tracce audio da usare in slideshow e video.")
    uploaded = st.file_uploader("Carica musica", accept_multiple_files=True, type=["mp3", "wav", "aac", "flac", "ogg", "m4a"], key="music_tab_uploader")
    if uploaded:
        for up in uploaded:
            _save_upload(up, "music")
        _refresh_library()
    music = library.list_music()
    if music:
        for m in music:
            st.audio(m)
    else:
        st.info("Nessun brano caricato.")

    # ── AI: Analisi tracce musicali ───────────────────────────────────────
    st.divider()
    with st.expander("🤖 AI: Mood e tag per le tracce musicali"):
        if music:
            _sel_track = st.selectbox(
                "Seleziona traccia da analizzare",
                music,
                format_func=lambda p: Path(p).name,
                key="ai_music_sel",
            )
            if st.button("🎵 Analizza mood con AI", key="ai_music_mood_btn"):
                with st.spinner("AI analizza la traccia..."):
                    _mname = Path(_sel_track).name if _sel_track else ""
                    st.session_state["ai_music_mood"] = ai.suggest_music_mood(_mname)
            if "ai_music_mood" in st.session_state:
                st.info(st.session_state["ai_music_mood"])

            if st.button("🎼 Analizza tutte le tracce", key="ai_music_all_btn"):
                _all_moods = {}
                for _tm in music:
                    with st.spinner(f"Analisi: {Path(_tm).name}..."):
                        _all_moods[Path(_tm).name] = ai.suggest_music_mood(Path(_tm).name)
                st.session_state["ai_music_all_moods"] = _all_moods

            if "ai_music_all_moods" in st.session_state:
                st.markdown("**Analisi AI di tutte le tracce:**")
                for _tn, _mood in st.session_state["ai_music_all_moods"].items():
                    st.markdown(f"**{_tn}:** {_mood}")
        else:
            st.info("Carica almeno una traccia musicale per l'analisi AI.")

# ══════════════════════════════════════════════════════════════════════════════
# Tab 10 — Riepilogo
# ══════════════════════════════════════════════════════════════════════════════
with tabs[10]:
    st.header("Riepilogo")
    st.markdown("Dashboard di controllo della tua libreria e attività.")
    imgs, vids, music = _refresh_library()
    edited_photos = library.list_edited("photos")
    edited_videos = library.list_edited("videos")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Foto originali", len(imgs))
    c2.metric("Video originali", len(vids))
    c3.metric("Foto modificate", len(edited_photos))
    c4.metric("Video prodotti", len(edited_videos))
    total_size = 0
    for f in (library.BASE).rglob("*"):
        if f.is_file():
            total_size += f.stat().st_size
    st.metric("Spazio occupato", f"{total_size / (1024*1024):.1f} MB")
    user_id = auth.current_user_id()
    if user_id:
        jobs = db.list_jobs(user_id)[:5]
        if jobs:
            st.markdown("### Ultimi lavori")
            for j in jobs:
                st.write(f"**{j[1]}** — {j[2][:60]} — _{j[4]}_")

    # ── AI: Analisi libreria ──────────────────────────────────────────────
    st.divider()
    with st.expander("🤖 AI: Analisi e consigli sulla libreria"):
        if st.button("📊 Analizza libreria con AI", key="ai_lib_report_btn"):
            _size_mb = total_size / (1024 * 1024)
            with st.spinner("AI analizza la tua libreria..."):
                st.session_state["ai_lib_report"] = ai.analyze_library(
                    n_photos=len(imgs),
                    n_videos=len(vids),
                    n_music=len(music),
                    n_edited_photos=len(edited_photos),
                    n_edited_videos=len(edited_videos),
                    size_mb=_size_mb,
                )
        if "ai_lib_report" in st.session_state:
            st.info(st.session_state["ai_lib_report"])

# ══════════════════════════════════════════════════════════════════════════════
# Tab 11 — Lavori
# ══════════════════════════════════════════════════════════════════════════════
with tabs[11]:
    st.header("Lavori salvati")
    st.markdown("Qui trovi foto e video modificati, pronti per essere scaricati o rivisti.")
    edited_photos = library.list_edited("photos")
    edited_videos = library.list_edited("videos")
    if edited_photos:
        st.subheader("Foto modificate")
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
                        st.download_button("Scarica", f, file_name=Path(edited_photos[idx]).name, key=f"dl_img_{idx}")
    if edited_videos:
        st.subheader("Video prodotti")
        for v in edited_videos:
            st.video(v)
            st.caption(Path(v).name)
            with open(v, "rb") as f:
                st.download_button("Scarica", f, file_name=Path(v).name, key=f"dl_vid_{v}")
    if not edited_photos and not edited_videos:
        st.info("Nessun lavoro salvato. Modifica foto o video per vederli qui.")

    # ── AI: Didascalie automatiche ────────────────────────────────────────
    if edited_photos:
        st.divider()
        with st.expander("🤖 AI: Genera didascalie per le foto modificate"):
            _cap_sel = st.selectbox(
                "Seleziona foto",
                edited_photos,
                format_func=lambda p: Path(p).name,
                key="ai_cap_sel",
            )
            if st.button("✍️ Genera didascalia AI", key="ai_cap_single_btn"):
                if _cap_sel and Path(_cap_sel).is_file():
                    with st.spinner("AI genera la didascalia..."):
                        _cap_text = ai.caption_photo(_cap_sel)
                        st.session_state[f"ai_cap_{Path(_cap_sel).stem}"] = _cap_text
            _cap_key = f"ai_cap_{Path(_cap_sel).stem}" if _cap_sel else None
            if _cap_key and _cap_key in st.session_state:
                st.success(f"📸 {st.session_state[_cap_key]}")

            if st.button("📸 Genera didascalie per tutte le foto", key="ai_cap_all_btn"):
                _all_caps = {}
                for _ep in edited_photos:
                    with st.spinner(f"AI: {Path(_ep).name}..."):
                        _all_caps[Path(_ep).name] = ai.caption_photo(_ep)
                st.session_state["ai_all_captions"] = _all_caps

            if "ai_all_captions" in st.session_state:
                st.markdown("**Didascalie AI:**")
                for _fn, _cap in st.session_state["ai_all_captions"].items():
                    st.markdown(f"- **{_fn}:** {_cap}")

# ══════════════════════════════════════════════════════════════════════════════
# Tab 12 — Photopea
# ══════════════════════════════════════════════════════════════════════════════
with tabs[12]:
    st.header("Photopea")
    st.markdown("Editor professionale integrato. Carica una foto, modificala, poi esportala e ricaricala nella Libreria.")
    st.info("Per usare Photopea: File > Open (o trascina un'immagine) → modifica → File > Export As > PNG/JPG.")

    # ── AI: Suggerisci passaggi di editing ────────────────────────────────
    with st.expander("🤖 AI: Suggerisci passaggi di editing in Photopea", expanded=True):
        _pp_imgs = st.session_state.get("library_images", []) + library.list_edited("photos")
        if _pp_imgs:
            _pp_sel = st.selectbox(
                "Seleziona una foto da analizzare",
                _pp_imgs,
                format_func=lambda p: Path(p).name,
                key="ai_pp_sel",
            )
            if st.button("🎨 Genera guida editing Photopea con AI", key="ai_pp_guide_btn"):
                if _pp_sel and Path(_pp_sel).is_file():
                    with st.spinner("AI analizza la foto e prepara la guida..."):
                        _pp_guide = ai.suggest_photopea_edits(_pp_sel)
                        st.session_state["ai_pp_guide"] = _pp_guide
                else:
                    st.warning("File non trovato.")
            if "ai_pp_guide" in st.session_state:
                st.info(st.session_state["ai_pp_guide"])
        else:
            st.info("Carica almeno una foto nella libreria per ricevere suggerimenti AI personalizzati.")

    st.components.v1.iframe("https://www.photopea.com", width=None, height=800, scrolling=True)

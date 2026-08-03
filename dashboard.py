"""AppFoto Studio — Enterprise Dashboard"""
import os
from pathlib import Path

import numpy as np
import streamlit as st

import ai_tools
import auth
import collage as collage_mod
import db
import duplicate_finder
import face_swap
import library
import photo_editor
import photo_enhancer
import projects as proj_mod
import video_editor
import video_merger
import video_slideshow

library.init_library()
proj_mod.init_projects()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _log(job_type, input_summary, output_path, status="ok"):
    user_id = auth.current_user_id()
    if user_id:
        db.log_job(user_id, job_type, input_summary, output_path, status)


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


def _current_project_photos():
    pf = st.session_state.get("active_project")
    if pf:
        return proj_mod.get_project_photos(pf)
    return st.session_state.get("library_images", [])


def _current_project_videos():
    pf = st.session_state.get("active_project")
    if pf:
        return proj_mod.get_project_videos(pf)
    return st.session_state.get("library_videos", [])


def _current_project_music():
    pf = st.session_state.get("active_project")
    if pf:
        return proj_mod.get_project_music(pf)
    return st.session_state.get("library_music", [])


def _list_files(folder, exts):
    p = Path(folder)
    if not p.is_dir():
        return []
    return sorted([str(f) for f in p.iterdir() if f.suffix.lower() in exts and f.is_file()])


# ---------------------------------------------------------------------------
# Page config & CSS
# ---------------------------------------------------------------------------

st.set_page_config(page_title="AppFoto Studio Enterprise", layout="wide", page_icon="🎨")
auth.require_login()

st.markdown("""
<style>
:root {
    --accent: #7c3aed;
    --accent2: #06b6d4;
    --accent-hover: #6d28d9;
    --bg: #0c0c0f;
    --surface: #13131a;
    --surface-2: #1c1c26;
    --surface-3: #242432;
    --border: #2d2d3d;
    --text: #f0f0f5;
    --muted: #9898b0;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
}
.stApp { background-color: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; }
h1, h2, h3 { color: var(--accent2); font-weight: 700; }
.main-header { text-align:center; padding: 1.5rem 0 0.5rem; }
.main-header h1 {
    font-size: 3.2rem; font-weight: 900; letter-spacing: -2px;
    background: linear-gradient(135deg, #7c3aed, #06b6d4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; text-shadow: none;
}
.main-header .tagline { color: var(--muted); font-size: 0.9rem; letter-spacing: 0.3em; text-transform: uppercase; margin-bottom: 1.5rem; }
.enterprise-badge {
    display: inline-block; background: linear-gradient(135deg,#7c3aed,#06b6d4);
    color: white; font-size: 0.65rem; font-weight: 800; letter-spacing: 0.2em;
    padding: 3px 10px; border-radius: 99px; text-transform: uppercase; vertical-align: middle; margin-left: 8px;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: var(--surface); padding: 0.5rem 0.8rem 0;
    border-radius: 12px 12px 0 0; border-bottom: 2px solid var(--border); flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
    background: var(--surface-2); color: var(--muted); border-radius: 8px 8px 0 0;
    padding: 10px 18px; font-weight: 600; border: 1px solid var(--border); border-bottom: none; font-size: 0.82rem;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,#7c3aed,#06b6d4); color: white;
    border-color: var(--accent); box-shadow: 0 -3px 12px rgba(124,58,237,0.35);
}
div.stButton > button {
    background: linear-gradient(135deg,#7c3aed,#06b6d4); color: white;
    border: none; border-radius: 8px; padding: 0.6rem 1.4rem;
    font-weight: 700; transition: 0.2s; box-shadow: 0 4px 14px rgba(124,58,237,0.3);
}
div.stButton > button:hover { opacity: 0.88; box-shadow: 0 6px 18px rgba(124,58,237,0.45); }
div.stButton > button[kind="secondary"] {
    background: var(--surface-2); color: var(--text); border: 1px solid var(--border); box-shadow: none;
}
div[data-testid="stTextInput"] label, div[data-testid="stNumberInput"] label,
div[data-testid="stSlider"] label, div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label { color: var(--text) !important; font-weight: 500; }
div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
    background: var(--surface-2) !important; color: var(--text) !important;
    border: 1px solid var(--border) !important; border-radius: 6px !important;
}
div[data-baseweb="select"] > div { background: var(--surface-2) !important; border-color: var(--border) !important; }
.stSidebar { background: var(--surface) !important; border-right: 1px solid var(--border); }
.stSidebar .stMetric { background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem; }
.card {
    background: var(--surface-2); border: 1px solid var(--border); border-radius: 12px;
    padding: 1.2rem; margin-bottom: 1rem;
}
.project-card {
    background: linear-gradient(135deg, var(--surface-2), var(--surface-3));
    border: 1px solid var(--border); border-radius: 12px; padding: 1rem; cursor: pointer;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.project-card:hover { border-color: var(--accent2); box-shadow: 0 0 0 1px var(--accent2); }
.project-card.active { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent); }
.stat-pill {
    display: inline-block; background: var(--surface-3); border-radius: 99px;
    padding: 2px 10px; font-size: 0.75rem; color: var(--muted); margin: 2px;
}
.tool-section { border-left: 3px solid var(--accent); padding-left: 1rem; margin-bottom: 1.5rem; }
.stInfo { background: var(--surface-2) !important; border-left: 4px solid var(--accent2) !important; }
.stSuccess { background: #071f12 !important; border-left: 4px solid var(--success) !important; }
.stError { background: #1f0707 !important; border-left: 4px solid var(--danger) !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
  <h1>AppFoto Studio <span class="enterprise-badge">Enterprise</span></h1>
  <div class="tagline">Piattaforma professionale per foto · video · audio</div>
</div>
""", unsafe_allow_html=True)

IMAGE_EXTS = library.IMAGE_EXTS
VIDEO_EXTS = library.VIDEO_EXTS
MUSIC_EXTS = library.MUSIC_EXTS


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.get('username', 'Utente')}")
    if auth.current_user_is_admin():
        st.markdown('<span style="color:#f59e0b;font-size:0.75rem">⭐ ADMIN</span>', unsafe_allow_html=True)
    st.divider()

    st.subheader("📁 Progetto attivo")
    all_projects = proj_mod.list_projects()
    proj_names = [p["name"] for p in all_projects]
    proj_folders = [p["folder"] for p in all_projects]
    active_proj_folder = st.session_state.get("active_project", "")

    with st.expander("Crea nuovo progetto"):
        np_name = st.text_input("Nome progetto", key="sb_new_proj_name")
        np_desc = st.text_input("Descrizione", key="sb_new_proj_desc")
        if st.button("➕ Crea", key="sb_create_proj"):
            if np_name:
                try:
                    proj_mod.create_project(np_name, np_desc)
                    st.success(f"Progetto '{np_name}' creato")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    if proj_folders:
        idx = proj_folders.index(active_proj_folder) if active_proj_folder in proj_folders else 0
        sel = st.selectbox("Progetto", proj_names, index=idx, key="sb_proj_select")
        sel_folder = proj_folders[proj_names.index(sel)]
        if st.button("📂 Apri progetto", key="sb_open_proj"):
            st.session_state.active_project = sel_folder
            st.rerun()
        if active_proj_folder:
            stats = proj_mod.get_project_stats(active_proj_folder)
            c1, c2 = st.columns(2)
            c1.metric("Foto", stats["photos"])
            c2.metric("Video", stats["videos"])
            c1.metric("Export", stats["exports"])
            c2.metric("MB", stats["size_mb"])
    else:
        st.info("Nessun progetto. Creane uno sopra.")

    st.divider()
    st.subheader("📚 Libreria globale")
    img_uploads = st.file_uploader("Carica foto", accept_multiple_files=True,
                                    type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"], key="lib_img_uploader")
    if img_uploads:
        paths = _save_uploads(img_uploads, "photos")
        for p in paths:
            db.log_upload(auth.current_user_id(), Path(p).name, p)

    vid_uploads = st.file_uploader("Carica video", accept_multiple_files=True,
                                    type=["mp4", "mov", "avi", "mkv"], key="lib_vid_uploader")
    if vid_uploads:
        paths = _save_uploads(vid_uploads, "videos")
        for p in paths:
            db.log_upload(auth.current_user_id(), Path(p).name, p)

    music_uploads = st.file_uploader("Carica musica", accept_multiple_files=True,
                                      type=["mp3", "wav", "aac", "flac", "ogg", "m4a"], key="lib_music_uploader")
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

    if st.button("🚪 Logout", key="logout_btn"):
        for k in ["authenticated", "username", "user_id", "is_admin", "active_project"]:
            st.session_state.pop(k, None)
        st.rerun()


# ---------------------------------------------------------------------------
# Image picker helper
# ---------------------------------------------------------------------------

def _image_picker(label, key, sources=None):
    if sources is None:
        sources = _current_project_photos()
    if not sources:
        st.info("Nessuna foto nella libreria/progetto. Carica dalla sidebar.")
        return None
    selected_key = f"selected_{key}"
    selected = st.session_state.get(selected_key)
    st.markdown(f"**{label}** — seleziona dalla libreria")
    for i in range(0, min(len(sources), 16), 4):
        cols = st.columns(4)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(sources):
                with col:
                    try:
                        st.image(sources[idx], use_container_width=True)
                    except Exception:
                        st.write(Path(sources[idx]).name)
                    if st.button("✔ Seleziona", key=f"sel_{key}_{idx}"):
                        st.session_state[selected_key] = sources[idx]
                        st.rerun()
    if selected:
        st.markdown(f"✅ Selezionato: **{Path(selected).name}**")
    return selected


def _file_or_upload(label, key, accept=None, kind="photos", sources=None):
    c1, c2 = st.columns([1, 1])
    with c1:
        uploaded = st.file_uploader(f"Carica {label}", type=accept, key=f"upl_{key}")
    with c2:
        path = st.text_input(f"Percorso manuale {label}", key=f"path_{key}")
    saved = _save_upload(uploaded, kind)
    if saved:
        db.log_upload(auth.current_user_id(), Path(saved).name, saved)
        _refresh_library()
        return saved
    selected = _image_picker(label, key, sources)
    if selected:
        return selected
    if path:
        resolved = Path(path).resolve()
        if resolved.is_file():
            return str(resolved)
        st.error(f"File non trovato: {path}")
    return ""


def _multi_picker(label, key, sources=None):
    if sources is None:
        sources = _current_project_photos()
    options = [Path(p).name for p in sources]
    selected_names = st.multiselect(label, options, key=f"mpick_{key}")
    name_to_path = {Path(p).name: p for p in sources}
    return [name_to_path[n] for n in selected_names if n in name_to_path]


# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------

TABS = [
    "🗂 Progetti",
    "📚 Libreria",
    "✏️ Editor Foto",
    "🤖 Strumenti AI",
    "💧 Testo & Watermark",
    "🖼 Collage",
    "✨ Migliora",
    "🎬 Slideshow",
    "🔗 Unisci Video",
    "✂️ Editor Video",
    "🎵 Musica",
    "🔍 Duplicati",
    "😶 Face Swap",
    "💾 Lavori",
    "📊 Riepilogo",
    "🕘 Storico",
    "⚙️ Admin",
    "🎨 Photopea",
]

tabs = st.tabs(TABS)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 0 — Progetti
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.header("🗂 Gestione Progetti")
    st.markdown("Organizza foto, video e audio in **progetti separati** con cartelle permanenti.")

    all_projects = proj_mod.list_projects()

    if not all_projects:
        st.info("Nessun progetto ancora. Crea il primo!")
    else:
        for p in all_projects:
            folder = p["folder"]
            is_active = folder == st.session_state.get("active_project", "")
            stats = proj_mod.get_project_stats(folder)
            with st.container():
                card_class = "project-card active" if is_active else "project-card"
                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
                c1, c2, c3 = st.columns([3, 4, 2])
                with c1:
                    st.markdown(f"### {'✅ ' if is_active else ''}{p['name']}")
                    st.caption(p.get("description", ""))
                with c2:
                    st.markdown(
                        f'<span class="stat-pill">📷 {stats["photos"]} foto</span>'
                        f'<span class="stat-pill">🎬 {stats["videos"]} video</span>'
                        f'<span class="stat-pill">📤 {stats["exports"]} export</span>'
                        f'<span class="stat-pill">💾 {stats["size_mb"]} MB</span>',
                        unsafe_allow_html=True
                    )
                with c3:
                    if st.button("📂 Apri", key=f"open_proj_{folder}"):
                        st.session_state.active_project = folder
                        st.rerun()
                    if not is_active:
                        if st.button("🗑 Elimina", key=f"del_proj_{folder}"):
                            proj_mod.delete_project(folder)
                            st.success(f"Progetto '{p['name']}' eliminato")
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            st.divider()

    st.subheader("➕ Nuovo progetto")
    with st.form("new_project_form"):
        col1, col2 = st.columns(2)
        with col1:
            np_name = st.text_input("Nome progetto *", key="np_name")
        with col2:
            np_desc = st.text_input("Descrizione", key="np_desc")
        submitted = st.form_submit_button("Crea progetto")
    if submitted:
        if np_name:
            try:
                proj_mod.create_project(np_name, np_desc)
                st.success(f"Progetto '{np_name}' creato con successo!")
                st.rerun()
            except Exception as e:
                st.error(str(e))
        else:
            st.error("Inserisci un nome per il progetto")

    active_folder = st.session_state.get("active_project")
    if active_folder:
        st.divider()
        st.subheader(f"📤 Carica nel progetto attivo: **{active_folder}**")
        c1, c2, c3 = st.columns(3)
        with c1:
            proj_imgs = st.file_uploader("Foto", accept_multiple_files=True,
                                          type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"], key="proj_img_up")
            if proj_imgs:
                for f in proj_imgs:
                    proj_mod.save_to_project(active_folder, f, "photos")
                st.success(f"Caricate {len(proj_imgs)} foto")
        with c2:
            proj_vids = st.file_uploader("Video", accept_multiple_files=True,
                                          type=["mp4", "mov", "avi", "mkv"], key="proj_vid_up")
            if proj_vids:
                for f in proj_vids:
                    proj_mod.save_to_project(active_folder, f, "videos")
                st.success(f"Caricati {len(proj_vids)} video")
        with c3:
            proj_music = st.file_uploader("Musica", accept_multiple_files=True,
                                           type=["mp3", "wav", "aac", "flac", "ogg"], key="proj_music_up")
            if proj_music:
                for f in proj_music:
                    proj_mod.save_to_project(active_folder, f, "music")
                st.success(f"Caricati {len(proj_music)} brani")

        proj_photos_list = proj_mod.get_project_photos(active_folder)
        if proj_photos_list:
            st.markdown("**Foto nel progetto:**")
            for i in range(0, min(len(proj_photos_list), 12), 4):
                cols = st.columns(4)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(proj_photos_list):
                        with col:
                            try:
                                st.image(proj_photos_list[idx], use_container_width=True)
                            except Exception:
                                pass
                            st.caption(Path(proj_photos_list[idx]).name)
                            if st.button("🗑", key=f"del_pf_{idx}"):
                                proj_mod.delete_file(proj_photos_list[idx])
                                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Libreria
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.header("📚 Libreria Permanente")
    st.markdown("Tutti i file caricati rimangono **permanentemente** nella libreria. Naviga, scarica o elimina.")

    imgs, vids, music = _refresh_library()

    lib_tab1, lib_tab2, lib_tab3 = st.tabs(["📷 Foto", "🎬 Video", "🎵 Musica"])

    with lib_tab1:
        if not imgs:
            st.info("Nessuna foto nella libreria globale. Carica dalla sidebar.")
        else:
            st.markdown(f"**{len(imgs)} foto originali**")
            search_img = st.text_input("🔍 Cerca per nome", key="lib_search_img")
            filtered = [p for p in imgs if search_img.lower() in Path(p).name.lower()] if search_img else imgs
            for i in range(0, len(filtered), 4):
                cols = st.columns(4)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(filtered):
                        with col:
                            try:
                                st.image(filtered[idx], use_container_width=True)
                            except Exception:
                                pass
                            st.caption(Path(filtered[idx]).name)
                            size_kb = Path(filtered[idx]).stat().st_size // 1024
                            st.markdown(f'<span class="stat-pill">{size_kb} KB</span>', unsafe_allow_html=True)
                            with open(filtered[idx], "rb") as ff:
                                st.download_button("⬇", ff, file_name=Path(filtered[idx]).name, key=f"lib_dl_img_{idx}")
                            if st.button("🗑", key=f"lib_del_img_{idx}"):
                                proj_mod.delete_file(filtered[idx])
                                st.rerun()
                            active_folder = st.session_state.get("active_project")
                            if active_folder:
                                if st.button("📂→Proj", key=f"lib_copy_proj_{idx}"):
                                    proj_mod.copy_to_project(active_folder, filtered[idx], "photos")
                                    st.success("Copiata nel progetto!")

    with lib_tab2:
        if not vids:
            st.info("Nessun video nella libreria globale.")
        else:
            st.markdown(f"**{len(vids)} video**")
            for v in vids:
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.video(v)
                    st.caption(Path(v).name)
                with c2:
                    with open(v, "rb") as ff:
                        st.download_button("⬇ Scarica", ff, file_name=Path(v).name, key=f"lib_dl_vid_{v}")
                with c3:
                    if st.button("🗑 Elimina", key=f"lib_del_vid_{v}"):
                        proj_mod.delete_file(v)
                        st.rerun()

    with lib_tab3:
        if not music:
            st.info("Nessuna musica nella libreria.")
        else:
            for m in music:
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.audio(m)
                    st.caption(Path(m).name)
                with c2:
                    if st.button("🗑", key=f"lib_del_mus_{m}"):
                        proj_mod.delete_file(m)
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Editor Foto
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.header("✏️ Editor Foto Professionale")
    st.markdown("Regolazioni complete in stile **Lightroom/Photoshop**: colore, tono, filtri, trasformazioni.")

    c1, c2 = st.columns(2)
    with c1:
        edit_input = _file_or_upload("foto", "edit_input",
                                      accept=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
                                      kind="photos", sources=_current_project_photos())
    with c2:
        edit_default = ""
        if edit_input:
            p = Path(edit_input)
            edit_default = str(library.EXPORTS / f"{p.stem}_edit_v1{p.suffix}")
        edit_output = st.text_input("File di uscita", value=edit_default, key="edit_output")

    # Preview
    if edit_input and Path(edit_input).is_file():
        try:
            st.image(edit_input, caption="Originale", use_container_width=True)
        except Exception as e:
            st.error(str(e))
    else:
        st.image(np.full((200, 400, 3), 30, dtype=np.uint8), caption="Seleziona un'immagine")

    # Controls in expandable sections
    with st.expander("📐 Trasformazioni", expanded=True):
        c3, c4, c5, c6, c7 = st.columns(5)
        with c3:
            edit_rotate = st.number_input("Rotazione (°)", value=0.0, step=90.0, key="edit_rotate")
        with c4:
            edit_width = st.number_input("Larghezza px", value=0, step=10, key="edit_width")
        with c5:
            edit_height = st.number_input("Altezza px", value=0, step=10, key="edit_height")
        with c6:
            edit_keep_aspect = st.checkbox("Mantieni proporzioni", value=True, key="edit_keep_aspect")
        with c7:
            edit_mirror_h = st.checkbox("↔ Specchio H", key="edit_mirror_h")
            edit_mirror_v = st.checkbox("↕ Specchio V", key="edit_mirror_v")

    with st.expander("🎨 Colore & Tono", expanded=True):
        c8, c9, c10, c11 = st.columns(4)
        with c8:
            edit_brightness = st.slider("Luminosità", 0.0, 3.0, 1.0, 0.05, key="edit_brightness")
        with c9:
            edit_contrast = st.slider("Contrasto", 0.0, 3.0, 1.0, 0.05, key="edit_contrast")
        with c10:
            edit_saturation = st.slider("Saturazione", 0.0, 3.0, 1.0, 0.05, key="edit_saturation")
        with c11:
            edit_sharpen = st.slider("Nitidezza", 0.0, 3.0, 0.0, 0.1, key="edit_sharpen")

    with st.expander("🌈 HSL & Avanzato"):
        c12, c13, c14 = st.columns(3)
        with c12:
            edit_hue = st.slider("Tonalità (hue)", -180, 180, 0, key="edit_hue")
        with c13:
            edit_hsl_sat = st.slider("Saturazione HSL", 0.0, 2.0, 1.0, 0.05, key="edit_hsl_sat")
        with c14:
            edit_light = st.slider("Luminosità HSL", -0.5, 0.5, 0.0, 0.02, key="edit_light")
        c15, c16 = st.columns(2)
        with c15:
            edit_vibrance = st.slider("Vibranza", -1.0, 1.0, 0.0, 0.05, key="edit_vibrance")
        with c16:
            edit_vignette = st.slider("Vignettatura", 0.0, 1.0, 0.0, 0.05, key="edit_vignette")

    with st.expander("📈 Curve"):
        curve_shadow = st.slider("Ombre", 0, 128, 0, key="edit_curve_shadow")
        curve_highlight = st.slider("Luci", 128, 255, 255, key="edit_curve_highlight")

    with st.expander("🎭 Bilanciamento colore"):
        c17, c18, c19 = st.columns(3)
        with c17:
            cb_sr = st.slider("R ombre", -50, 50, 0, key="cb_sr")
            cb_sg = st.slider("G ombre", -50, 50, 0, key="cb_sg")
            cb_sb = st.slider("B ombre", -50, 50, 0, key="cb_sb")
        with c18:
            cb_mr = st.slider("R mezzitoni", -50, 50, 0, key="cb_mr")
            cb_mg = st.slider("G mezzitoni", -50, 50, 0, key="cb_mg")
            cb_mb = st.slider("B mezzitoni", -50, 50, 0, key="cb_mb")
        with c19:
            cb_hr = st.slider("R luci", -50, 50, 0, key="cb_hr")
            cb_hg = st.slider("G luci", -50, 50, 0, key="cb_hg")
            cb_hb = st.slider("B luci", -50, 50, 0, key="cb_hb")

    with st.expander("🎭 Filtri artistici"):
        c20, c21, c22 = st.columns(3)
        with c20:
            edit_filter = st.selectbox("Filtro", ["nessuno", "grayscale", "sepia", "blur", "sharpen", "emboss", "edge", "contour"], key="edit_filter")
        with c21:
            edit_duotone = st.checkbox("Duotono", key="edit_duotone")
        with c22:
            if edit_duotone:
                edit_dt1 = st.color_picker("Colore ombre", "#1a1a2e", key="edit_dt1")
                edit_dt2 = st.color_picker("Colore luci", "#f2c94c", key="edit_dt2")
            else:
                edit_dt1 = "#1a1a2e"
                edit_dt2 = "#f2c94c"

    def _edit_kwargs():
        kw = {
            "rotate": edit_rotate,
            "brightness": edit_brightness,
            "contrast": edit_contrast,
            "saturation": edit_saturation,
            "sharpen": edit_sharpen,
            "mirror_h": edit_mirror_h,
            "mirror_v": edit_mirror_v,
        }
        if edit_width:
            kw["width"] = edit_width
        if edit_height:
            kw["height"] = edit_height
        kw["keep_aspect"] = edit_keep_aspect
        if edit_filter != "nessuno":
            kw["filter"] = edit_filter
        if curve_shadow != 0 or curve_highlight != 255:
            kw["curves"] = [(0, curve_shadow), (128, 128), (255, curve_highlight)]
        cbs = (cb_sr, cb_sg, cb_sb)
        cbm = (cb_mr, cb_mg, cb_mb)
        cbh = (cb_hr, cb_hg, cb_hb)
        if any(v != 0 for v in cbs + cbm + cbh):
            kw["color_balance"] = (cbs, cbm, cbh)
        if edit_hue != 0 or edit_hsl_sat != 1.0 or edit_light != 0.0:
            kw["hsl"] = (edit_hue, edit_hsl_sat, edit_light)
        if edit_vibrance != 0:
            kw["vibrance"] = edit_vibrance
        if edit_vignette != 0:
            kw["vignette"] = edit_vignette
        if edit_duotone:
            kw["duotone"] = (edit_dt1, edit_dt2)
        return kw

    ce1, ce2, ce3 = st.columns(3)
    with ce1:
        preview_btn = st.button("👁️ Anteprima", key="edit_preview")
    with ce2:
        save_btn = st.button("💾 Salva", key="edit_save")
    with ce3:
        save_proj_btn = st.button("📂 Salva nel progetto", key="edit_save_proj")

    if preview_btn:
        if edit_input and Path(edit_input).is_file():
            with st.spinner("Elaborazione..."):
                try:
                    prev_path = str(library.EDITED_PHOTOS / f"_preview_{Path(edit_input).stem}.jpg")
                    photo_editor.process_image(edit_input, prev_path, **_edit_kwargs())
                    st.image(prev_path, caption="Anteprima", use_container_width=True)
                except Exception as e:
                    st.error(str(e))
        else:
            st.warning("Seleziona prima un'immagine")

    if save_btn:
        if edit_input and edit_output:
            with st.spinner("Salvataggio..."):
                try:
                    out = library.next_version(edit_output)
                    photo_editor.process_image(edit_input, out, **_edit_kwargs())
                    st.image(out, caption="Salvata", use_container_width=True)
                    st.success(f"Salvata in: {out}")
                    _log("photo_edit", edit_input, out)
                    _refresh_library()
                    with open(out, "rb") as ff:
                        st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                except Exception as e:
                    st.error(str(e))
        else:
            st.error("Seleziona foto e percorso di uscita")

    if save_proj_btn:
        active_folder = st.session_state.get("active_project")
        if not active_folder:
            st.error("Nessun progetto attivo. Aprilo dalla sidebar o dal tab Progetti.")
        elif edit_input and Path(edit_input).is_file():
            with st.spinner("Salvataggio nel progetto..."):
                try:
                    out_dir = proj_mod.get_project_path(active_folder) / "exports"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    stem = Path(edit_input).stem
                    out = library.next_version(str(out_dir / f"{stem}_edit.jpg"))
                    photo_editor.process_image(edit_input, out, **_edit_kwargs())
                    st.success(f"Salvata nel progetto: {Path(out).name}")
                    _log("photo_edit", edit_input, out)
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Strumenti AI
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.header("🤖 Strumenti AI & Avanzati")
    st.markdown("Correzioni automatiche, effetti avanzati, e miglioramenti intelligenti.")

    ai_tab1, ai_tab2, ai_tab3 = st.tabs(["🔧 Correzioni Auto", "🎨 Effetti Artistici", "📈 Upscaling"])

    with ai_tab1:
        ai_in = _file_or_upload("foto", "ai_in", accept=["jpg", "jpeg", "png", "webp"],
                                 kind="photos", sources=_current_project_photos())
        if ai_in:
            st.image(ai_in, caption="Originale", use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            do_noise = st.checkbox("Riduzione rumore", key="ai_noise")
            noise_str = st.slider("Intensità rumore", 1, 3, 1, key="ai_noise_str") if do_noise else 1
            do_autolevel = st.checkbox("Auto livelli (per canale)", key="ai_autolevel")
            do_wb = st.checkbox("Bilanciamento bianco automatico", key="ai_wb")
        with col_b:
            do_autocontrast = st.checkbox("Auto contrasto", key="ai_autocontrast")
            do_sharpen = st.checkbox("Smart sharpen (unsharp mask)", key="ai_sharpen")
            sharpen_amount = st.slider("Forza sharpen", 0.5, 3.0, 1.5, 0.1, key="ai_sharpen_amount") if do_sharpen else 1.5
            do_dehaze = st.checkbox("Rimozione foschia", key="ai_dehaze")
            dehaze_str = st.slider("Forza dehaze", 0.1, 1.0, 0.5, 0.05, key="ai_dehaze_str") if do_dehaze else 0.5
            do_hdr = st.checkbox("Effetto HDR", key="ai_hdr")

        ai_out = st.text_input("File di uscita", value=str(library.EXPORTS / "ai_result_v1.jpg"), key="ai_out")

        if st.button("✨ Applica correzioni AI", key="ai_run"):
            if not ai_in or not Path(ai_in).is_file():
                st.error("Seleziona un'immagine")
            else:
                with st.spinner("Elaborazione AI..."):
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(ai_in).convert("RGB")
                        if do_noise:
                            img = ai_tools.noise_reduction(img, noise_str)
                        if do_wb:
                            img = ai_tools.auto_white_balance(img)
                        if do_autolevel:
                            img = ai_tools.auto_level(img)
                        if do_autocontrast:
                            img = ai_tools.auto_contrast(img)
                        if do_sharpen:
                            img = ai_tools.smart_sharpen(img, sharpen_amount)
                        if do_dehaze:
                            img = ai_tools.dehaze(img, dehaze_str)
                        if do_hdr:
                            img = ai_tools.hdr_effect(img)
                        out = library.next_version(ai_out)
                        Path(out).parent.mkdir(parents=True, exist_ok=True)
                        img.save(out, quality=96)
                        st.image(out, caption="Risultato", use_container_width=True)
                        st.success(f"Salvato: {out}")
                        _log("ai_enhance", ai_in, out)
                        with open(out, "rb") as ff:
                            st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                    except Exception as e:
                        st.error(str(e))

    with ai_tab2:
        art_in = _file_or_upload("foto", "art_in", accept=["jpg", "jpeg", "png", "webp"],
                                  kind="photos", sources=_current_project_photos())
        if art_in:
            st.image(art_in, caption="Originale", use_container_width=True)
        effect = st.selectbox("Effetto artistico", [
            "vintage", "hdr", "pencil_sketch", "oil_paint", "cross_process"
        ], key="art_effect")
        art_out = st.text_input("File uscita", value=str(library.EXPORTS / "art_v1.jpg"), key="art_out")

        if st.button("🎨 Applica effetto", key="art_run"):
            if not art_in or not Path(art_in).is_file():
                st.error("Seleziona un'immagine")
            else:
                with st.spinner("Elaborazione effetto..."):
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(art_in).convert("RGB")
                        if effect == "vintage":
                            img = ai_tools.vintage_effect(img)
                        elif effect == "hdr":
                            img = ai_tools.hdr_effect(img)
                        elif effect == "pencil_sketch":
                            img = ai_tools.pencil_sketch(img)
                        elif effect == "oil_paint":
                            img = ai_tools.oil_paint_effect(img)
                        elif effect == "cross_process":
                            img = ai_tools.cross_process(img)
                        out = library.next_version(art_out)
                        Path(out).parent.mkdir(parents=True, exist_ok=True)
                        img.save(out, quality=96)
                        st.image(out, caption=f"Effetto: {effect}", use_container_width=True)
                        st.success(f"Salvato: {out}")
                        _log("art_effect", art_in, out)
                        with open(out, "rb") as ff:
                            st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                    except Exception as e:
                        st.error(str(e))

    with ai_tab3:
        up_in = _file_or_upload("foto da ingrandire", "up_in", accept=["jpg", "jpeg", "png", "webp"],
                                 kind="photos", sources=_current_project_photos())
        if up_in and Path(up_in).is_file():
            from PIL import Image as PILImage
            try:
                _pi = PILImage.open(up_in)
                st.info(f"Dimensione originale: {_pi.width} × {_pi.height} px")
                st.image(up_in, use_container_width=True)
            except Exception:
                pass
        scale_factor = st.selectbox("Fattore di ingrandimento", [2, 3, 4], key="up_scale")
        up_out = st.text_input("File uscita", value=str(library.EXPORTS / "upscaled_v1.jpg"), key="up_out")
        if st.button("🔍 Ingrandisci", key="up_run"):
            if not up_in or not Path(up_in).is_file():
                st.error("Seleziona un'immagine")
            else:
                with st.spinner(f"Upscaling ×{scale_factor}..."):
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(up_in).convert("RGB")
                        img = ai_tools.upscale(img, scale_factor)
                        out = library.next_version(up_out)
                        Path(out).parent.mkdir(parents=True, exist_ok=True)
                        img.save(out, quality=96)
                        st.image(out, caption=f"Ingrandita ×{scale_factor}: {img.width}×{img.height}", use_container_width=True)
                        st.success(f"Salvata: {out}")
                        _log("upscale", up_in, out)
                        with open(out, "rb") as ff:
                            st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                    except Exception as e:
                        st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Testo & Watermark
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.header("💧 Testo & Watermark")
    st.markdown("Aggiungi testi, loghi e watermark alle foto con opacità e posizione personalizzabili.")

    wm_tab1, wm_tab2 = st.tabs(["📝 Watermark testo", "🖼 Watermark logo"])

    with wm_tab1:
        wt_in = _file_or_upload("foto", "wt_in", accept=["jpg", "jpeg", "png", "webp"],
                                 kind="photos", sources=_current_project_photos())
        if wt_in and Path(wt_in).is_file():
            st.image(wt_in, caption="Originale", use_container_width=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            wt_text = st.text_input("Testo watermark", value="© Studio", key="wt_text")
        with c2:
            wt_pos = st.selectbox("Posizione", ["bottom-right", "bottom-left", "top-right", "top-left",
                                                  "center", "bottom-center", "top-center"], key="wt_pos")
        with c3:
            wt_size = st.slider("Dimensione font", 20, 120, 48, key="wt_size")
        c4, c5 = st.columns(2)
        with c4:
            wt_color = st.color_picker("Colore testo", "#ffffff", key="wt_color")
        with c5:
            wt_opacity = st.slider("Opacità", 50, 255, 180, key="wt_opacity")
        wt_shadow = st.checkbox("Ombra testo", value=True, key="wt_shadow")
        wt_out = st.text_input("File uscita", value=str(library.EXPORTS / "watermark_v1.jpg"), key="wt_out")
        if st.button("💧 Applica watermark testo", key="wt_run"):
            if not wt_in or not Path(wt_in).is_file():
                st.error("Seleziona un'immagine")
            else:
                with st.spinner("Applicazione watermark..."):
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(wt_in).convert("RGB")
                        r = int(wt_color[1:3], 16)
                        g = int(wt_color[3:5], 16)
                        b = int(wt_color[5:7], 16)
                        img = ai_tools.add_text_watermark(img, wt_text, wt_pos, wt_size,
                                                           (r, g, b), wt_opacity, wt_shadow)
                        out = library.next_version(wt_out)
                        Path(out).parent.mkdir(parents=True, exist_ok=True)
                        img.save(out, quality=96)
                        st.image(out, caption="Con watermark", use_container_width=True)
                        st.success(f"Salvato: {out}")
                        _log("watermark_text", wt_in, out)
                        with open(out, "rb") as ff:
                            st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                    except Exception as e:
                        st.error(str(e))

    with wm_tab2:
        wl_base = _file_or_upload("foto base", "wl_base", accept=["jpg", "jpeg", "png", "webp"],
                                   kind="photos", sources=_current_project_photos())
        wl_logo = _file_or_upload("logo (PNG con trasparenza)", "wl_logo",
                                   accept=["png", "webp"], kind="photos", sources=_current_project_photos())
        if wl_base and Path(wl_base).is_file():
            st.image(wl_base, caption="Foto base", use_container_width=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            wl_pos = st.selectbox("Posizione logo", ["bottom-right", "bottom-left", "top-right", "top-left", "center"], key="wl_pos")
        with c2:
            wl_scale = st.slider("Dimensione logo (%)", 5, 50, 20, key="wl_scale")
        with c3:
            wl_opacity = st.slider("Opacità logo", 50, 255, 150, key="wl_opacity")
        wl_out = st.text_input("File uscita", value=str(library.EXPORTS / "logo_wm_v1.jpg"), key="wl_out")
        if st.button("🖼 Applica logo watermark", key="wl_run"):
            if not wl_base or not wl_logo:
                st.error("Seleziona foto base e logo")
            else:
                with st.spinner("Applicazione logo..."):
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(wl_base).convert("RGB")
                        img = ai_tools.add_image_watermark(img, wl_logo, wl_pos, wl_scale / 100, wl_opacity)
                        out = library.next_version(wl_out)
                        Path(out).parent.mkdir(parents=True, exist_ok=True)
                        img.save(out, quality=96)
                        st.image(out, caption="Con logo", use_container_width=True)
                        st.success(f"Salvato: {out}")
                        _log("watermark_logo", wl_base, out)
                        with open(out, "rb") as ff:
                            st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                    except Exception as e:
                        st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Collage
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.header("🖼 Creatore di Collage")
    st.markdown("Componi collage professionali da più foto in layout **griglia, strip, o featured**.")

    coll_tab1, coll_tab2, coll_tab3 = st.tabs(["📷 Griglia", "↔ Strip", "⭐ Featured"])

    with coll_tab1:
        cg_photos = _multi_picker("Seleziona foto per il collage", "cg_photos", _current_project_photos())
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            cg_cols = st.number_input("Colonne", 1, 6, 3, key="cg_cols")
        with c2:
            cg_cell_w = st.number_input("Larghezza cella px", 200, 1200, 600, 50, key="cg_cell_w")
        with c3:
            cg_cell_h = st.number_input("Altezza cella px", 150, 900, 450, 50, key="cg_cell_h")
        with c4:
            cg_padding = st.number_input("Padding px", 0, 50, 12, key="cg_padding")
        c5, c6 = st.columns(2)
        with c5:
            cg_fit = st.selectbox("Adattamento", ["fill", "fit"], key="cg_fit")
        with c6:
            cg_labels = st.checkbox("Mostra nomi file", key="cg_labels")
        cg_bg = st.color_picker("Colore sfondo", "#0f0f0f", key="cg_bg")
        cg_out = st.text_input("File collage", value=str(library.EXPORTS / "collage_grid_v1.jpg"), key="cg_out")
        if st.button("🖼 Crea collage griglia", key="cg_run"):
            if not cg_photos:
                st.error("Seleziona almeno 2 foto")
            else:
                with st.spinner("Creazione collage..."):
                    try:
                        r = int(cg_bg[1:3], 16)
                        g = int(cg_bg[3:5], 16)
                        b = int(cg_bg[5:7], 16)
                        out = library.next_version(cg_out)
                        collage_mod.make_grid_collage(cg_photos, out, cg_cols, cg_cell_w, cg_cell_h,
                                                       cg_padding, (r, g, b), cg_fit, cg_labels)
                        st.image(out, caption="Collage griglia", use_container_width=True)
                        st.success(f"Salvato: {out}")
                        _log("collage_grid", str(cg_photos), out)
                        with open(out, "rb") as ff:
                            st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                    except Exception as e:
                        st.error(str(e))

    with coll_tab2:
        cs_photos = _multi_picker("Foto per strip", "cs_photos", _current_project_photos())
        c1, c2, c3 = st.columns(3)
        with c1:
            cs_dir = st.selectbox("Direzione", ["horizontal", "vertical"], key="cs_dir")
        with c2:
            cs_size = st.number_input("Altezza/larghezza px", 200, 1200, 500, 50, key="cs_size")
        with c3:
            cs_pad = st.number_input("Spazio tra foto px", 0, 50, 10, key="cs_pad")
        cs_bg = st.color_picker("Sfondo", "#0f0f0f", key="cs_bg")
        cs_out = st.text_input("File uscita", value=str(library.EXPORTS / "collage_strip_v1.jpg"), key="cs_out")
        if st.button("↔ Crea strip", key="cs_run"):
            if not cs_photos:
                st.error("Seleziona almeno 2 foto")
            else:
                with st.spinner("Creazione strip..."):
                    try:
                        r = int(cs_bg[1:3], 16)
                        g = int(cs_bg[3:5], 16)
                        b = int(cs_bg[5:7], 16)
                        out = library.next_version(cs_out)
                        collage_mod.make_strip_collage(cs_photos, out, cs_dir, cs_size, cs_pad, (r, g, b))
                        st.image(out, caption="Strip collage", use_container_width=True)
                        st.success(f"Salvato: {out}")
                        _log("collage_strip", str(cs_photos), out)
                        with open(out, "rb") as ff:
                            st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                    except Exception as e:
                        st.error(str(e))

    with coll_tab3:
        cf_photos = _multi_picker("Foto (prima = in evidenza)", "cf_photos", _current_project_photos())
        c1, c2, c3 = st.columns(3)
        with c1:
            cf_w = st.number_input("Larghezza canvas px", 800, 3840, 1920, 80, key="cf_w")
        with c2:
            cf_h = st.number_input("Altezza canvas px", 450, 2160, 1080, 40, key="cf_h")
        with c3:
            cf_pad = st.number_input("Padding px", 0, 50, 10, key="cf_pad")
        cf_bg = st.color_picker("Sfondo", "#0f0f0f", key="cf_bg")
        cf_out = st.text_input("File uscita", value=str(library.EXPORTS / "collage_featured_v1.jpg"), key="cf_out")
        if st.button("⭐ Crea layout featured", key="cf_run"):
            if not cf_photos:
                st.error("Seleziona almeno 2 foto")
            else:
                with st.spinner("Creazione collage featured..."):
                    try:
                        r = int(cf_bg[1:3], 16)
                        g = int(cf_bg[3:5], 16)
                        b = int(cf_bg[5:7], 16)
                        out = library.next_version(cf_out)
                        collage_mod.make_featured_collage(cf_photos, out, cf_w, cf_h, cf_pad, (r, g, b))
                        st.image(out, caption="Featured collage", use_container_width=True)
                        st.success(f"Salvato: {out}")
                        _log("collage_featured", str(cf_photos), out)
                        with open(out, "rb") as ff:
                            st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                    except Exception as e:
                        st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — Migliora foto (batch)
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.header("✨ Migliora Foto (Batch)")
    st.markdown("Ottimizza esposizione, contrasto e nitidezza su **più foto contemporaneamente**.")
    c1, c2 = st.columns(2)
    with c1:
        enh_batch = st.multiselect("Seleziona foto", _current_project_photos() or library.list_originals("photos"), key="enh_batch")
        if not enh_batch:
            enh_folder = st.text_input("Oppure cartella", key="enh_folder")
        else:
            enh_folder = ""
    with c2:
        enh_out = st.text_input("Cartella di uscita", value=str(library.EDITED_PHOTOS), key="enh_out")
    c3, c4, c5 = st.columns(3)
    with c3:
        gamma = st.number_input("Gamma", 0.1, 3.0, 1.2, 0.1, key="enh_gamma")
    with c4:
        sharp = st.number_input("Nitidezza", 0.0, 3.0, 1.0, 0.1, key="enh_sharp")
    with c5:
        blur_th = st.number_input("Soglia sfocatura", 0.0, 500.0, 100.0, 10.0, key="enh_blur")
    if st.button("✨ Migliora foto selezionate", key="enh_run"):
        targets = enh_batch or ([enh_folder] if enh_folder and Path(enh_folder).is_dir() else [])
        if not targets or not enh_out:
            st.error("Seleziona foto o cartella e percorso di uscita")
        else:
            with st.spinner(f"Elaborazione {len(enh_batch) if enh_batch else 'cartella'}..."):
                try:
                    if enh_batch:
                        photo_enhancer.enhance_files(enh_batch, enh_out, gamma, sharp, blur_th)
                    else:
                        photo_enhancer.enhance_folder(enh_folder, enh_out, gamma, sharp, blur_th)
                    st.success(f"Foto migliorate salvate in: {enh_out}")
                    _log("enhance", str(targets), enh_out)
                    _refresh_library()
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 7 — Slideshow
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.header("🎬 Crea Slideshow")
    st.markdown("Genera un video con transizioni a dissolvenza dalle tue foto.")
    c1, c2 = st.columns(2)
    with c1:
        sld_photos = _multi_picker("Foto per lo slideshow", "sld_photos", _current_project_photos())
        if not sld_photos:
            sld_folder = st.text_input("Oppure cartella foto", key="sld_folder")
        else:
            sld_folder = ""
    with c2:
        sld_output = st.text_input("File video uscita", value=str(library.EDITED_VIDEOS / "slideshow_v1.mp4"), key="sld_output")
    c3, c4, c5, c6 = st.columns(4)
    with c3:
        sld_dur = st.number_input("Durata immagine (s)", 0.5, 30.0, 3.0, 0.5, key="sld_dur")
    with c4:
        sld_trans = st.number_input("Transizione (s)", 0.0, 5.0, 0.5, 0.1, key="sld_trans")
    with c5:
        sld_fps = st.number_input("FPS", 10, 60, 30, key="sld_fps")
    with c6:
        sld_res = st.selectbox("Risoluzione", ["1920x1080", "1280x720", "3840x2160", "1080x1080"], key="sld_res")
    all_music = (proj_mod.get_project_music(st.session_state.get("active_project", ""))
                  or library.list_music())
    sld_music = st.selectbox("Musica di sottofondo (opzionale)", [""] + all_music, key="sld_music")
    if st.button("▶ Crea slideshow", key="sld_run"):
        paths = sld_photos or _list_files(sld_folder, IMAGE_EXTS)
        if not paths:
            st.error("Nessuna immagine trovata")
        else:
            with st.spinner("Creazione slideshow in corso..."):
                try:
                    out = library.next_version(sld_output)
                    video_slideshow.make_slideshow(paths, out, sld_dur, sld_trans, sld_res, int(sld_fps), sld_music or None)
                    st.success(f"Slideshow salvato: {out}")
                    st.video(out)
                    _log("slideshow", str(paths), out)
                    with open(out, "rb") as ff:
                        st.download_button("⬇️ Scarica video", ff, file_name=Path(out).name)
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 8 — Unione Video
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[8]:
    st.header("🔗 Unisci Video")
    st.markdown("Concatena più clip in un unico video normalizzando risoluzione e framerate.")
    c1, c2 = st.columns(2)
    with c1:
        mrg_vids = st.multiselect("Video da unire", _current_project_videos() or library.list_originals("videos"), key="mrg_vids")
        if not mrg_vids:
            mrg_folder = st.text_input("Oppure cartella video", key="mrg_folder")
        else:
            mrg_folder = ""
    with c2:
        mrg_output = st.text_input("File unito", value=str(library.EDITED_VIDEOS / "merged_v1.mp4"), key="mrg_output")
    c3, c4 = st.columns(2)
    with c3:
        mrg_res = st.selectbox("Risoluzione", ["1920x1080", "1280x720", "3840x2160"], key="mrg_res")
    with c4:
        mrg_fps = st.number_input("FPS", 1, 60, 30, key="mrg_fps")
    if st.button("🔗 Unisci video", key="mrg_run"):
        paths = mrg_vids or _list_files(mrg_folder, VIDEO_EXTS)
        if not paths:
            st.error("Nessun video trovato")
        else:
            with st.spinner("Unione in corso..."):
                try:
                    out = library.next_version(mrg_output)
                    video_merger.merge_videos(paths, out, mrg_res, int(mrg_fps))
                    st.success(f"Video unito: {out}")
                    st.video(out)
                    _log("merge", str(paths), out)
                    with open(out, "rb") as ff:
                        st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 9 — Editor Video
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[9]:
    st.header("✂️ Editor Video Avanzato")
    st.markdown("Taglia, filtra, aggiungi audio, testo, cambia velocità e converti in GIF.")

    all_proj_vids = _current_project_videos() or library.list_originals("videos")
    vid_op = st.selectbox("Operazione", [
        "✂️ Taglia",
        "🎵 Aggiungi musica",
        "🔇 Rimuovi audio",
        "🔊 Regola volume",
        "🎭 Applica filtro",
        "⚡ Cambia velocità",
        "📝 Aggiungi testo/titolo",
        "🎞 Estrai frame",
        "🔊 Estrai audio",
        "🌀 Video in GIF",
    ], key="vid_op")

    c1, c2 = st.columns(2)
    with c1:
        vid_src_select = st.selectbox("Video dalla libreria", [""] + all_proj_vids,
                                       format_func=lambda x: Path(x).name if x else "-- seleziona --", key="vid_src_select")
        vid_upload = st.file_uploader("Oppure carica video", type=["mp4", "mov", "avi", "mkv"], key="vid_upload_new")
    if vid_upload:
        vid_input = _save_upload(vid_upload, "videos")
    elif vid_src_select:
        vid_input = vid_src_select
    else:
        vid_input = ""
    with c2:
        vid_output = st.text_input("File di uscita", value=str(library.EDITED_VIDEOS / "output_v1.mp4"), key="vid_output")

    if vid_input and Path(vid_input).is_file():
        try:
            info = video_editor.get_video_info(vid_input)
            st.info(f"Video: {info.get('width')}×{info.get('height')}px | {info.get('fps')} fps | {info.get('duration_sec')} sec")
        except Exception:
            pass

    if "Taglia" in vid_op:
        ca, cb = st.columns(2)
        with ca:
            start_t = st.number_input("Inizio (s)", 0.0, 9999.0, 0.0, 0.5, key="vid_start")
        with cb:
            end_t = st.number_input("Fine (s)", 0.0, 9999.0, 10.0, 0.5, key="vid_end")
        if st.button("✂️ Taglia", key="vid_trim_btn"):
            with st.spinner("Taglio..."):
                try:
                    out = library.next_version(vid_output)
                    video_editor.trim_video(vid_input, out, start_t, end_t)
                    st.success(f"Tagliato: {out}")
                    st.video(out)
                    _log("video_trim", vid_input, out)
                    with open(out, "rb") as ff:
                        st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                except Exception as e:
                    st.error(str(e))

    elif "Aggiungi musica" in vid_op:
        audio_file = st.selectbox("File audio", [""] + library.list_music(), key="vid_audio_sel")
        loop_audio = st.checkbox("Ripeti audio se più corto del video", key="vid_loop")
        if st.button("🎵 Aggiungi musica", key="vid_music_btn"):
            if not audio_file:
                st.error("Seleziona un file audio dalla libreria")
            else:
                with st.spinner("Aggiunta audio..."):
                    try:
                        out = library.next_version(vid_output)
                        video_editor.add_music_to_video(vid_input, audio_file, out, loop_audio)
                        st.success(f"Audio aggiunto: {out}")
                        st.video(out)
                        _log("video_music", vid_input, out)
                        with open(out, "rb") as ff:
                            st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                    except Exception as e:
                        st.error(str(e))

    elif "Rimuovi audio" in vid_op:
        if st.button("🔇 Rimuovi audio", key="vid_mute_btn"):
            with st.spinner("Rimozione audio..."):
                try:
                    out = library.next_version(vid_output)
                    video_editor.mute_video(vid_input, out)
                    st.success(f"Audio rimosso: {out}")
                    st.video(out)
                    _log("video_mute", vid_input, out)
                except Exception as e:
                    st.error(str(e))

    elif "Regola volume" in vid_op:
        vol = st.slider("Volume (1.0 = originale)", 0.0, 4.0, 1.0, 0.05, key="vid_vol")
        if st.button("🔊 Applica volume", key="vid_vol_btn"):
            with st.spinner("Regolazione volume..."):
                try:
                    out = library.next_version(vid_output)
                    video_editor.set_volume(vid_input, out, vol)
                    st.success(f"Volume impostato a {vol}: {out}")
                    st.video(out)
                    _log("video_volume", vid_input, out)
                    with open(out, "rb") as ff:
                        st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                except Exception as e:
                    st.error(str(e))

    elif "filtro" in vid_op:
        flt = st.selectbox("Filtro", ["grayscale", "blur", "negate", "edgedetect", "vignette", "sharpen"], key="vid_filter")
        if st.button("🎭 Applica filtro", key="vid_filter_btn"):
            with st.spinner("Filtro in corso..."):
                try:
                    out = library.next_version(vid_output)
                    video_editor.apply_filter(vid_input, out, flt)
                    st.success(f"Filtro {flt} applicato: {out}")
                    st.video(out)
                    _log("video_filter", vid_input, out)
                    with open(out, "rb") as ff:
                        st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                except Exception as e:
                    st.error(str(e))

    elif "velocità" in vid_op:
        speed = st.slider("Velocità (1.0 = normale, 2.0 = doppia, 0.5 = slow-mo)", 0.25, 4.0, 1.0, 0.25, key="vid_speed")
        if st.button("⚡ Applica velocità", key="vid_speed_btn"):
            with st.spinner("Cambio velocità..."):
                try:
                    out = library.next_version(vid_output)
                    video_editor.change_speed(vid_input, out, speed)
                    st.success(f"Velocità ×{speed} applicata: {out}")
                    st.video(out)
                    _log("video_speed", vid_input, out)
                    with open(out, "rb") as ff:
                        st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                except Exception as e:
                    st.error(str(e))

    elif "testo" in vid_op or "titolo" in vid_op:
        vt_text = st.text_input("Testo da sovrapporre", "Il mio video", key="vt_text")
        c1, c2, c3 = st.columns(3)
        with c1:
            vt_pos = st.selectbox("Posizione", ["bottom", "top", "center", "top-left", "bottom-right"], key="vt_pos")
        with c2:
            vt_size = st.slider("Dimensione font", 20, 120, 48, key="vt_size")
        with c3:
            vt_color = st.selectbox("Colore", ["white", "yellow", "red", "black", "cyan"], key="vt_color")
        c4, c5 = st.columns(2)
        with c4:
            vt_start = st.number_input("Inizio (s, 0=tutto)", 0.0, 9999.0, 0.0, 0.5, key="vt_start")
        with c5:
            vt_end = st.number_input("Fine (s, -1=fino alla fine)", -1.0, 9999.0, -1.0, 0.5, key="vt_end")
        if st.button("📝 Aggiungi testo", key="vt_run"):
            with st.spinner("Aggiunta testo..."):
                try:
                    out = library.next_version(vid_output)
                    video_editor.add_text_overlay(vid_input, out, vt_text, vt_pos, vt_size, vt_color, vt_start, vt_end)
                    st.success(f"Testo aggiunto: {out}")
                    st.video(out)
                    _log("video_text", vid_input, out)
                    with open(out, "rb") as ff:
                        st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                except Exception as e:
                    st.error(str(e))

    elif "frame" in vid_op:
        interval = st.number_input("Ogni quanti secondi estrarre un frame", 0.1, 60.0, 1.0, 0.1, key="vid_interval")
        frames_out = st.text_input("Cartella frame", value=str(library.EXPORTS / "frames"), key="vid_frames_out")
        if st.button("🎞 Estrai frame", key="vid_frames_btn"):
            with st.spinner("Estrazione frame..."):
                try:
                    video_editor.extract_frames(vid_input, frames_out, interval)
                    frames = sorted(Path(frames_out).glob("*.jpg"))
                    st.success(f"Estratti {len(frames)} frame in {frames_out}")
                    _log("video_frames", vid_input, frames_out)
                    for i in range(0, min(len(frames), 8), 4):
                        cols = st.columns(4)
                        for j, col in enumerate(cols):
                            if i + j < len(frames):
                                with col:
                                    st.image(str(frames[i + j]), use_container_width=True)
                except Exception as e:
                    st.error(str(e))

    elif "audio" in vid_op and "Estrai" in vid_op:
        audio_out = st.text_input("File audio uscita (.mp3)", value=str(library.EXPORTS / "audio_v1.mp3"), key="vid_audio_out")
        if st.button("🔊 Estrai audio", key="vid_extract_audio_btn"):
            with st.spinner("Estrazione audio..."):
                try:
                    out = library.next_version(audio_out)
                    video_editor.extract_audio(vid_input, out)
                    st.success(f"Audio estratto: {out}")
                    st.audio(out)
                    _log("video_extract_audio", vid_input, out)
                    with open(out, "rb") as ff:
                        st.download_button("⬇️ Scarica audio", ff, file_name=Path(out).name)
                except Exception as e:
                    st.error(str(e))

    elif "GIF" in vid_op:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            gif_fps = st.number_input("FPS GIF", 5, 30, 10, key="gif_fps")
        with c2:
            gif_scale = st.number_input("Larghezza px", 200, 1280, 480, 40, key="gif_scale")
        with c3:
            gif_start = st.number_input("Inizio (s)", 0.0, 9999.0, 0.0, 0.5, key="gif_start")
        with c4:
            gif_dur = st.number_input("Durata (s)", 1.0, 60.0, 5.0, 0.5, key="gif_dur")
        gif_out = st.text_input("File GIF", value=str(library.EXPORTS / "output_v1.gif"), key="gif_out")
        if st.button("🌀 Crea GIF", key="gif_run"):
            with st.spinner("Creazione GIF..."):
                try:
                    out = library.next_version(gif_out)
                    video_editor.video_to_gif(vid_input, out, int(gif_fps), int(gif_scale), gif_start, gif_dur)
                    st.success(f"GIF creata: {out}")
                    st.image(out)
                    _log("video_gif", vid_input, out)
                    with open(out, "rb") as ff:
                        st.download_button("⬇️ Scarica GIF", ff, file_name=Path(out).name)
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 10 — Musica
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[10]:
    st.header("🎵 Libreria Musica")
    st.markdown("Gestisci tracce audio per slideshow, video e montaggi.")
    mus_uploads = st.file_uploader("Carica musica", accept_multiple_files=True,
                                    type=["mp3", "wav", "aac", "flac", "ogg", "m4a"], key="music_tab_up")
    if mus_uploads:
        for f in mus_uploads:
            _save_upload(f, "music")
        _refresh_library()
    all_music_list = library.list_music()
    if all_music_list:
        for m in all_music_list:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.audio(m)
                st.caption(f"{Path(m).name}  |  {Path(m).stat().st_size // 1024} KB")
            with c2:
                if st.button("🗑", key=f"del_mus_{m}"):
                    proj_mod.delete_file(m)
                    st.rerun()
    else:
        st.info("Nessun brano nella libreria. Carica file audio sopra.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 11 — Duplicati
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[11]:
    st.header("🔍 Rilevamento Duplicati")
    st.markdown("Trova e rimuovi foto duplicate o quasi identiche tramite hashing percettivo.")
    c1, c2 = st.columns(2)
    with c1:
        dup_folder = st.text_input("Cartella da scansionare", value=str(library.ORIGINAL_PHOTOS), key="dup_folder")
    with c2:
        dup_threshold = st.slider("Soglia distanza Hamming", 0, 20, 10, key="dup_threshold")
    if st.button("🔍 Cerca duplicati", key="dup_search"):
        if not Path(dup_folder).is_dir():
            st.error("Cartella non trovata")
        else:
            with st.spinner("Scansione..."):
                try:
                    report = duplicate_finder.find_and_report(dup_folder, dup_threshold, False, None)
                    st.success(f"Trovati **{report['duplicate_groups']}** gruppi su {report['total_images']} immagini")
                    _log("duplicates", dup_folder, "", "ok")
                    for i, group in enumerate(report['groups'], 1):
                        st.subheader(f"Gruppo {i} — migliore: {Path(group['best']).name}")
                        cols = st.columns(4)
                        for j, fp in enumerate(group['duplicates']):
                            with cols[j % 4]:
                                try:
                                    st.image(fp, use_container_width=True)
                                except Exception:
                                    pass
                                st.caption(Path(fp).name)
                except Exception as e:
                    st.error(str(e))
    if st.button("🗑 Elimina copie a risoluzione minore", key="dup_delete"):
        if not Path(dup_folder).is_dir():
            st.error("Cartella non trovata")
        else:
            with st.spinner("Eliminazione..."):
                try:
                    duplicate_finder.find_and_report(dup_folder, dup_threshold, True, None)
                    st.success("Copie duplicate eliminate")
                    _log("duplicates_delete", dup_folder, "", "ok")
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 12 — Face Swap
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[12]:
    st.header("😶 Face Swap")
    st.warning("Usa solo foto di tua proprietà e con pieno consenso delle persone ritratte.")
    c1, c2 = st.columns(2)
    with c1:
        face_src = _file_or_upload("foto sorgente (volto da usare)", "face_src",
                                    accept=["jpg", "jpeg", "png", "webp"], kind="photos",
                                    sources=_current_project_photos())
    with c2:
        face_dst = _file_or_upload("foto destinazione", "face_dst",
                                    accept=["jpg", "jpeg", "png", "webp"], kind="photos",
                                    sources=_current_project_photos())
    if face_src and Path(face_src).is_file():
        st.image(face_src, caption="Sorgente", use_container_width=True)
    if face_dst and Path(face_dst).is_file():
        st.image(face_dst, caption="Destinazione", use_container_width=True)
    face_out = st.text_input("Foto di output", value=str(library.EXPORTS / "face_swap_v1.jpg"), key="face_out")
    consent = st.checkbox("✅ Confermo di avere i diritti e il consenso per entrambe le immagini", key="face_consent")
    if st.button("😶 Scambia volto", key="face_run"):
        if not consent:
            st.error("Devi confermare il consenso.")
        elif not face_src or not face_dst:
            st.error("Seleziona entrambe le foto")
        else:
            with st.spinner("Face swap in corso..."):
                try:
                    out = library.next_version(face_out)
                    face_swap.swap_face(face_src, face_dst, out)
                    st.image(out, caption="Risultato", use_container_width=True)
                    st.success(f"Salvato: {out}")
                    _log("face_swap", f"{face_src}->{face_dst}", out)
                    with open(out, "rb") as ff:
                        st.download_button("⬇️ Scarica", ff, file_name=Path(out).name)
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 13 — Lavori salvati
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[13]:
    st.header("💾 Lavori Salvati")
    st.markdown("Foto modificate, video prodotti, collage ed esportazioni — pronti da scaricare.")

    saved_tab1, saved_tab2, saved_tab3 = st.tabs(["📷 Foto", "🎬 Video & GIF", "📤 Esportazioni"])

    with saved_tab1:
        edited_photos = library.list_edited("photos")
        exp_photos = [str(f) for f in library.EXPORTS.glob("*") if f.suffix.lower() in IMAGE_EXTS and f.is_file()]
        all_saved_photos = sorted(set(edited_photos + exp_photos))
        if all_saved_photos:
            for i in range(0, len(all_saved_photos), 4):
                cols = st.columns(4)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(all_saved_photos):
                        with col:
                            try:
                                st.image(all_saved_photos[idx], use_container_width=True)
                            except Exception:
                                pass
                            st.caption(Path(all_saved_photos[idx]).name)
                            with open(all_saved_photos[idx], "rb") as ff:
                                st.download_button("⬇️", ff, file_name=Path(all_saved_photos[idx]).name,
                                                    key=f"dl_ep_{idx}")
                            if st.button("🗑", key=f"del_ep_{idx}"):
                                proj_mod.delete_file(all_saved_photos[idx])
                                st.rerun()
        else:
            st.info("Nessuna foto modificata ancora.")

    with saved_tab2:
        edited_videos = library.list_edited("videos")
        if edited_videos:
            for v in edited_videos:
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.video(v)
                    st.caption(Path(v).name)
                with c2:
                    with open(v, "rb") as ff:
                        st.download_button("⬇️", ff, file_name=Path(v).name, key=f"dl_ev_{v}")
                    if st.button("🗑", key=f"del_ev_{v}"):
                        proj_mod.delete_file(v)
                        st.rerun()
        else:
            st.info("Nessun video prodotto ancora.")

    with saved_tab3:
        exp_files = sorted([str(f) for f in library.EXPORTS.glob("*") if f.is_file()])
        if exp_files:
            for f in exp_files:
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(Path(f).name)
                    try:
                        if Path(f).suffix.lower() in IMAGE_EXTS:
                            st.image(f, use_container_width=True)
                        elif Path(f).suffix.lower() in VIDEO_EXTS:
                            st.video(f)
                    except Exception:
                        pass
                with c2:
                    with open(f, "rb") as ff:
                        st.download_button("⬇️", ff, file_name=Path(f).name, key=f"dl_exp_{f}")
                    if st.button("🗑", key=f"del_exp_{f}"):
                        proj_mod.delete_file(f)
                        st.rerun()
        else:
            st.info("Nessuna esportazione ancora.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 14 — Riepilogo
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[14]:
    st.header("📊 Dashboard Riepilogo")
    imgs, vids, music = _refresh_library()
    edited_p = library.list_edited("photos")
    edited_v = library.list_edited("videos")
    all_projects_list = proj_mod.list_projects()
    total_size = sum(f.stat().st_size for f in library.BASE.rglob("*") if f.is_file())
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📷 Foto originali", len(imgs))
    c2.metric("🎬 Video originali", len(vids))
    c3.metric("✏️ Foto modificate", len(edited_p))
    c4.metric("📽 Video prodotti", len(edited_v))
    c5.metric("💾 Spazio totale", f"{total_size / (1024*1024):.1f} MB")

    st.divider()
    st.subheader("🗂 Progetti")
    if all_projects_list:
        proj_stats = [(p["name"], proj_mod.get_project_stats(p["folder"])) for p in all_projects_list]
        for pname, pstats in proj_stats:
            st.markdown(
                f"**{pname}** — "
                f"📷 {pstats['photos']} | 🎬 {pstats['videos']} | 📤 {pstats['exports']} | 💾 {pstats['size_mb']} MB"
            )
    else:
        st.info("Nessun progetto creato.")

    user_id = auth.current_user_id()
    if user_id:
        jobs = db.list_jobs(user_id)[:10]
        if jobs:
            st.divider()
            st.subheader("🕘 Ultimi lavori")
            for j in jobs:
                st.write(f"**{j[1]}** — {str(j[2])[:50]} — _{j[4]}_")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 15 — Storico
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[15]:
    st.header("🕘 Storico Lavori")
    user_id = auth.current_user_id()
    if auth.current_user_is_admin():
        show_all = st.checkbox("Mostra tutti gli utenti", key="show_all_jobs")
        jobs = db.list_jobs() if show_all else db.list_jobs(user_id)
    else:
        jobs = db.list_jobs(user_id)
    if not jobs:
        st.info("Nessun lavoro trovato.")
    else:
        cols = ["id", "tipo", "input", "output", "stato", "data"]
        if auth.current_user_is_admin() and st.session_state.get("show_all_jobs"):
            cols = ["id", "utente", "tipo", "input", "output", "stato", "data"]
        data = {c: [] for c in cols}
        for row in jobs:
            if auth.current_user_is_admin() and st.session_state.get("show_all_jobs"):
                data["id"].append(row[0])
                data["utente"].append(row[1])
                data["tipo"].append(row[2])
                data["input"].append(str(row[3])[:80])
                data["output"].append(str(row[4])[:80])
                data["stato"].append(row[5])
                data["data"].append(row[6])
            else:
                data["id"].append(row[0])
                data["tipo"].append(row[1])
                data["input"].append(str(row[2])[:80])
                data["output"].append(str(row[3])[:80])
                data["stato"].append(row[4])
                data["data"].append(row[5])
        st.dataframe(data, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 16 — Admin
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[16]:
    st.header("⚙️ Pannello Admin")
    if not auth.current_user_is_admin():
        st.error("Accesso riservato agli admin.")
    else:
        admin_tab1, admin_tab2 = st.tabs(["👥 Utenti", "🗄 Sistema"])

        with admin_tab1:
            with st.form("create_user_form"):
                st.markdown("### ➕ Crea utente")
                c1, c2, c3 = st.columns(3)
                with c1:
                    new_user = st.text_input("Username", key="admin_new_user")
                with c2:
                    new_pwd = st.text_input("Password", type="password", key="admin_new_pwd")
                with c3:
                    is_admin_new = st.checkbox("Admin", key="admin_is_admin")
                create_btn = st.form_submit_button("Crea utente")
            if create_btn:
                if not new_user or not new_pwd:
                    st.error("Username e password obbligatori")
                elif db.user_exists(new_user):
                    st.error("Username già esistente")
                else:
                    if db.create_user(new_user, new_pwd, is_admin_new):
                        st.success(f"Utente '{new_user}' creato")
                    else:
                        st.error("Errore nella creazione")

            users = db.list_users()
            if users:
                st.markdown("### 👥 Utenti esistenti")
                u_data = {"ID": [], "Username": [], "Admin": [], "Creato": []}
                for u in users:
                    u_data["ID"].append(u[0])
                    u_data["Username"].append(u[1])
                    u_data["Admin"].append("⭐ Sì" if u[2] else "No")
                    u_data["Creato"].append(str(u[3]))
                st.dataframe(u_data, use_container_width=True)
                del_id = st.number_input("ID utente da eliminare", 0, step=1, key="admin_del_id")
                if st.button("🗑 Elimina utente", key="admin_del_btn"):
                    if del_id == auth.current_user_id():
                        st.error("Non puoi eliminare te stesso")
                    elif db.delete_user(del_id):
                        st.success(f"Utente {del_id} eliminato")
                    else:
                        st.error("Errore nell'eliminazione")

        with admin_tab2:
            st.markdown("### 🗄 Informazioni sistema")
            total_size = sum(f.stat().st_size for f in library.BASE.rglob("*") if f.is_file())
            st.metric("Spazio totale libreria", f"{total_size / (1024*1024):.1f} MB")
            st.metric("Foto originali", len(library.list_originals("photos")))
            st.metric("Video originali", len(library.list_originals("videos")))
            st.metric("Progetti", len(proj_mod.list_projects()))
            st.markdown(f"**Percorso libreria:** `{library.BASE.resolve()}`")
            st.markdown(f"**Percorso progetti:** `{proj_mod.PROJECTS_BASE.resolve()}`")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 17 — Photopea
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[17]:
    st.header("🎨 Photopea — Editor Professionale")
    st.markdown("""
    **Photopea** è un editor fotografico professionale completo nel browser (gratuito, nessuna installazione).

    **Come usarlo:**
    1. Vai su **File → Open** e carica la tua foto (dalla libreria, scaricala prima)
    2. Modifica come in Photoshop (livelli, maschere, filtri, testo, pennelli...)
    3. Quando hai finito: **File → Export As → PNG/JPG**
    4. Ricarica il file esportato nella Libreria dalla sidebar
    """)
    st.info("Usa la sidebar per caricare/scaricare le foto da usare in Photopea.")
    st.components.v1.iframe("https://www.photopea.com", width=None, height=850, scrolling=True)

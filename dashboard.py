import os
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


st.set_page_config(page_title="AppFoto Studio", layout="wide")
auth.require_login()

st.markdown("""
<style>
    .stApp {
        background-color: #0a0a0a;
        color: #f1f1f1;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3 {
        color: #d4af37;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 600;
    }
    .main-header {
        text-align: center;
        margin-top: -1rem;
        margin-bottom: 0.2rem;
    }
    .main-header h1 {
        font-size: 3.2rem;
        font-weight: 700;
        color: #d4af37;
        letter-spacing: -1px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.6);
    }
    .sub-header {
        text-align: center;
        color: #a0a0a0;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #121212;
        padding: 0.5rem 1rem 0 1rem;
        border-radius: 12px 12px 0 0;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #151515;
        color: #d4d4d4;
        border-radius: 10px 10px 0 0;
        padding: 12px 28px;
        font-weight: 600;
        border: 1px solid #333333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #d4af37;
        color: #0a0a0a;
        border-color: #d4af37;
    }
    div.stButton > button:first-child {
        background-color: #d4af37;
        color: #0a0a0a;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 700;
        transition: 0.2s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div.stButton > button:hover {
        background-color: #c5a028;
        color: #0a0a0a;
        box-shadow: 0 6px 10px rgba(0,0,0,0.4);
    }
    div.stButton > button:active {
        background-color: #b08d1e;
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stSlider"] label,
    div[data-testid="stSelectbox"] label {
        color: #d4d4d4 !important;
        font-weight: 500;
    }
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stSelectbox"] > div > div {
        background-color: #151515 !important;
        color: #f1f1f1 !important;
        border: 1px solid #333333 !important;
        border-radius: 6px !important;
    }
    div[data-testid="stSlider"] > div > div > div {
        color: #d4af37 !important;
    }
    div[data-testid="stSlider"] [role="slider"] {
        background-color: #d4af37 !important;
    }
    .stMarkdown, .stInfo, .stSuccess, .stError, .stWarning {
        color: #f1f1f1;
    }
    .stInfo {
        background-color: #1a1a1a;
        border-left: 4px solid #d4af37;
    }
    .stSuccess {
        background-color: #1a2f1a;
        border-left: 4px solid #4ade80;
    }
    .stError {
        background-color: #2f1a1a;
        border-left: 4px solid #f87171;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>AppFoto Studio</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Gestione foto e video professionale in un clic</div>', unsafe_allow_html=True)

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
    st.info("Inserisci i percorsi delle cartelle o dei file, configura i parametri e premi il pulsante per eseguire.")

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}


def _list_files(folder, exts):
    p = Path(folder)
    if not p.is_dir():
        return []
    return sorted([str(f) for f in p.iterdir() if f.suffix.lower() in exts and f.is_file()])


tabs = st.tabs(["Duplicati", "Migliora foto", "Slideshow", "Unione video", "Editor Video", "Editor Foto", "Face Swap"])

with tabs[0]:
    st.header("Rilevamento foto duplicate")
    st.markdown("Trova foto duplicate o quasi identiche tramite hashing percettivo.")
    dup_folder = st.text_input("Cartella immagini", key="dup_folder")
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

with tabs[1]:
    st.header("Migliora foto")
    st.markdown("Correggi esposizione, contrasto e nitidezza delle immagini.")
    c1, c2 = st.columns(2)
    with c1:
        enh_in = st.text_input("Cartella foto in ingresso", key="enh_in")
    with c2:
        enh_out = st.text_input("Cartella foto in uscita", key="enh_out")
    c3, c4, c5 = st.columns(3)
    with c3:
        gamma = st.number_input("Gamma", value=1.2, step=0.1, min_value=0.1, key="enh_gamma")
    with c4:
        sharp = st.number_input("Nitidezza", value=1.0, step=0.1, min_value=0.0, key="enh_sharp")
    with c5:
        blur = st.number_input("Soglia sfocatura", value=100.0, step=10.0, min_value=0.0, key="enh_blur")
    if st.button("Migliora foto", key="enh_run"):
        if not enh_in or not enh_out:
            st.error("Inserisci entrambe le cartelle")
        else:
            with st.spinner("Elaborazione in corso..."):
                try:
                    photo_enhancer.enhance_folder(enh_in, enh_out, gamma, sharp, blur)
                except Exception as e:
                    st.error(str(e))
                else:
                    st.success(f"Foto migliorate salvate in: {enh_out}")

with tabs[2]:
    st.header("Crea slideshow da foto")
    st.markdown("Genera un video con transizioni a dissolvenza a partire dalle tue foto.")
    c1, c2 = st.columns(2)
    with c1:
        sld_input = st.text_input("Cartella foto (o percorsi separati da virgola)", key="sld_input")
    with c2:
        sld_output = st.text_input("File video di output", value="slideshow.mp4", key="sld_output")
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
        sld_music = st.text_input("Musica di sottofondo (opzionale)", key="sld_music")
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
                    video_slideshow.make_slideshow(paths, sld_output, sld_duration, sld_transition, sld_resolution, sld_fps, sld_music or None)
                except Exception as e:
                    st.error(str(e))
                else:
                    st.success(f"Slideshow salvato in: {sld_output}")

with tabs[3]:
    st.header("Unisci video")
    st.markdown("Concatena piu clip in un unico video normalizzando risoluzione e framerate.")
    c1, c2 = st.columns(2)
    with c1:
        mrg_input = st.text_input("Cartella video (o percorsi separati da virgola)", key="mrg_input")
    with c2:
        mrg_output = st.text_input("File video unito", value="merged.mp4", key="mrg_output")
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
                    video_merger.merge_videos(paths, mrg_output, mrg_resolution, mrg_fps)
                except Exception as e:
                    st.error(str(e))
                else:
                    st.success(f"Video unito salvato in: {mrg_output}")

with tabs[4]:
    st.header("Editor Video")
    st.markdown("Taglia clip, aggiungi musica, applica filtri artistici ed estrai frame.")
    operation = st.selectbox("Operazione", ["Taglia", "Aggiungi musica", "Applica filtro", "Estrai frame"], key="vid_op")
    c1, c2 = st.columns(2)
    with c1:
        vid_input = st.text_input("Video di ingresso", key="vid_input")
    with c2:
        vid_output = st.text_input("File/cartella di uscita", value="output.mp4", key="vid_output")
    if operation == "Taglia":
        c3, c4 = st.columns(2)
        with c3:
            start_t = st.number_input("Inizio (s)", value=0.0, min_value=0.0, step=0.1, key="vid_start")
        with c4:
            end_t = st.number_input("Fine (s)", value=10.0, min_value=0.0, step=0.1, key="vid_end")
        if st.button("Taglia video", key="vid_trim"):
            with st.spinner("Taglio in corso..."):
                try:
                    video_editor.trim_video(vid_input, vid_output, start_t, end_t)
                    st.success(f"Video tagliato: {vid_output}")
                except Exception as e:
                    st.error(str(e))
    elif operation == "Aggiungi musica":
        audio_file = st.text_input("File audio", key="vid_audio")
        loop_audio = st.checkbox("Ripeti audio se piu corto del video", key="vid_loop")
        if st.button("Aggiungi musica", key="vid_music_btn"):
            with st.spinner("Aggiunta audio..."):
                try:
                    video_editor.add_music_to_video(vid_input, audio_file, vid_output, loop_audio)
                    st.success(f"Audio aggiunto: {vid_output}")
                except Exception as e:
                    st.error(str(e))
    elif operation == "Applica filtro":
        filter_name = st.selectbox("Filtro", ["grayscale", "blur", "negate", "edgedetect", "vignette", "sharpen"], key="vid_filter")
        if st.button("Applica filtro", key="vid_filter_btn"):
            with st.spinner("Applicazione filtro..."):
                try:
                    video_editor.apply_filter(vid_input, vid_output, filter_name)
                    st.success(f"Filtro applicato: {vid_output}")
                except Exception as e:
                    st.error(str(e))
    elif operation == "Estrai frame":
        interval = st.number_input("Intervallo in secondi", value=1.0, min_value=0.1, step=0.1, key="vid_interval")
        if st.button("Estrai frame", key="vid_frames"):
            with st.spinner("Estrazione frame..."):
                try:
                    video_editor.extract_frames(vid_input, vid_output, interval)
                    st.success(f"Frame estratti in: {vid_output}")
                except Exception as e:
                    st.error(str(e))

with tabs[5]:
    st.header("Editor Foto")
    st.markdown("Ritaglia, ruota, ridimensiona e applica correzioni alle foto.")
    c1, c2 = st.columns(2)
    with c1:
        edit_input = st.text_input("Foto in ingresso", key="edit_input")
    with c2:
        edit_output = st.text_input("Foto in uscita", key="edit_output")
    if edit_input and Path(edit_input).is_file():
        try:
            preview = photo_editor.load_image(edit_input)
            st.image(preview, caption="Anteprima originale", use_container_width=True)
        except Exception as e:
            st.error(str(e))
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
        st.markdown(" ")
        st.markdown(" ")
    if st.button("Applica modifiche", key="edit_run"):
        if not edit_input or not edit_output:
            st.error("Inserisci foto in ingresso e in uscita")
        else:
            with st.spinner("Elaborazione in corso..."):
                try:
                    kwargs = {
                        "rotate": edit_rotate,
                        "brightness": edit_brightness,
                        "contrast": edit_contrast,
                        "saturation": edit_saturation,
                        "sharpen": edit_sharpen,
                    }
                    if edit_width:
                        kwargs["width"] = edit_width
                    if edit_height:
                        kwargs["height"] = edit_height
                    kwargs["keep_aspect"] = edit_keep_aspect
                    if edit_filter != "nessuno":
                        kwargs["filter"] = edit_filter
                    photo_editor.process_image(edit_input, edit_output, **kwargs)
                    st.image(photo_editor.load_image(edit_output), caption="Anteprima risultato", use_container_width=True)
                    st.success(f"Foto salvata in: {edit_output}")
                except Exception as e:
                    st.error(str(e))

with tabs[6]:
    st.header("Face Swap")
    st.markdown("Scambia il volto sorgente con quello in una foto destinazione. Usa solo foto di tua proprietà e con consenso.")
    st.warning("Il risultato include un watermark 'GENERATED' ed è destinato a scopi leciti e creativi.")
    c1, c2 = st.columns(2)
    with c1:
        face_src = st.text_input("Foto volto sorgente", key="face_src")
    with c2:
        face_dst = st.text_input("Foto corpo/volto destinazione", key="face_dst")
    face_out = st.text_input("Foto di output", value="face_swap_output.jpg", key="face_out")
    consent = st.checkbox("Confermo di avere i diritti e il consenso per entrambe le immagini", key="face_consent")
    if st.button("Scambia volto", key="face_run"):
        if not consent:
            st.error("Devi confermare i diritti e il consenso per procedere.")
        elif not face_src or not face_dst or not face_out:
            st.error("Inserisci tutti i percorsi")
        else:
            with st.spinner("Scambio volto in corso..."):
                try:
                    out_path = face_swap.swap_face(face_src, face_dst, face_out)
                    st.image(photo_editor.load_image(out_path), caption="Risultato", use_container_width=True)
                    st.success(f"Foto salvata in: {out_path}")
                except Exception as e:
                    st.error(str(e))

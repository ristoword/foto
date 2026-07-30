import os
import streamlit as st
from pathlib import Path

import duplicate_finder
import photo_enhancer
import video_slideshow
import video_merger


st.set_page_config(page_title="AppFoto Dashboard", layout="wide")
st.title("AppFoto Dashboard")

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv'}


def _list_files(folder, exts):
    p = Path(folder)
    if not p.is_dir():
        return []
    return sorted([str(f) for f in p.iterdir() if f.suffix.lower() in exts and f.is_file()])


tabs = st.tabs(["Duplicati", "Migliora foto", "Slideshow", "Unione video"])

with tabs[0]:
    st.header("Rilevamento foto duplicate")
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
                        st.subheader(f"Gruppo {i} - migliore: {Path(group['best']).name}")
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
                                    st.success("Copie duplicate eliminate. E' rimasta solo quella con risoluzione maggiore per gruppo.")

with tabs[1]:
    st.header("Migliora foto")
    enh_in = st.text_input("Cartella foto in ingresso", key="enh_in")
    enh_out = st.text_input("Cartella foto in uscita", key="enh_out")
    c1, c2, c3 = st.columns(3)
    with c1:
        gamma = st.number_input("Gamma", value=1.2, step=0.1, min_value=0.1, key="enh_gamma")
    with c2:
        sharp = st.number_input("Nitidezza", value=1.0, step=0.1, min_value=0.0, key="enh_sharp")
    with c3:
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
    sld_input = st.text_input("Cartella foto (o percorsi separati da virgola)", key="sld_input")
    sld_output = st.text_input("File video di output", value="slideshow.mp4", key="sld_output")
    c1, c2, c3 = st.columns(3)
    with c1:
        sld_duration = st.number_input("Durata immagine (s)", value=3.0, min_value=0.1, step=0.5, key="sld_duration")
    with c2:
        sld_transition = st.number_input("Transizione (s)", value=0.5, min_value=0.0, step=0.1, key="sld_transition")
    with c3:
        sld_fps = st.number_input("FPS", value=30, min_value=1, step=1, key="sld_fps")
    sld_resolution = st.selectbox("Risoluzione", ["1920x1080", "1280x720", "3840x2160"], key="sld_resolution")
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
    mrg_input = st.text_input("Cartella video (o percorsi separati da virgola)", key="mrg_input")
    mrg_output = st.text_input("File video unito", value="merged.mp4", key="mrg_output")
    c1, c2 = st.columns(2)
    with c1:
        mrg_resolution = st.selectbox("Risoluzione", ["1920x1080", "1280x720", "3840x2160"], key="mrg_resolution")
    with c2:
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

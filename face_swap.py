import cv2
import numpy as np
from pathlib import Path


def _detect_faces(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    faces = cascade.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
    return faces


def _largest_face(faces):
    if len(faces) == 0:
        return None
    return max(faces, key=lambda f: f[2] * f[3])


def _make_oval_mask(size):
    mask = np.zeros(size, dtype=np.uint8)
    center = (size[1] // 2, size[0] // 2)
    axes = (size[1] // 2 - 4, size[0] // 2 - 4)
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
    return mask


def _add_watermark(img, text="GENERATED - APPFOTO"):
    h, w = img.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = max(0.4, w / 1200)
    thickness = max(1, int(scale * 2))
    size = cv2.getTextSize(text, font, scale, thickness)[0]
    x = w - size[0] - 20
    y = h - 20
    # sfondo semi-trasparente
    overlay = img.copy()
    cv2.rectangle(overlay, (x - 10, y - size[1] - 10), (w - 10, y + 10), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
    cv2.putText(img, text, (x, y), font, scale, (212, 175, 55), thickness, cv2.LINE_AA)
    return img


def swap_face(src_path, dst_path, out_path, blend=0.85):
    src = cv2.imread(str(src_path), cv2.IMREAD_COLOR)
    dst = cv2.imread(str(dst_path), cv2.IMREAD_COLOR)
    if src is None:
        raise FileNotFoundError(f"Immagine sorgente non trovata: {src_path}")
    if dst is None:
        raise FileNotFoundError(f"Immagine destinazione non trovata: {dst_path}")

    src_faces = _detect_faces(src)
    dst_faces = _detect_faces(dst)
    if len(src_faces) == 0:
        raise ValueError("Nessun volto rilevato nella foto sorgente.")
    if len(dst_faces) == 0:
        raise ValueError("Nessun volto rilevato nella foto destinazione.")

    sx, sy, sw, sh = _largest_face(src_faces)
    dx, dy, dw, dh = _largest_face(dst_faces)

    # estrai volto sorgente e ridimensiona alla destinazione
    src_face = src[sy:sy + sh, sx:sx + sw]
    src_face = cv2.resize(src_face, (dw, dh), interpolation=cv2.INTER_LANCZOS4)

    # maschera ovale per clonaggio morbido
    mask = _make_oval_mask((dh, dw))

    # centro del volto destinazione
    center = (dx + dw // 2, dy + dh // 2)

    # clonaggio Poisson se le dimensioni consentono
    try:
        mixed = cv2.seamlessClone(src_face, dst, mask, center, cv2.NORMAL_CLONE)
    except cv2.error:
        # fallback: copia semplice con maschera ovale
        mixed = dst.copy()
        roi = mixed[dy:dy + dh, dx:dx + dw]
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
        blended = roi * (1 - mask_3ch * blend) + src_face * (mask_3ch * blend)
        mixed[dy:dy + dh, dx:dx + dw] = blended.astype(np.uint8)

    mixed = _add_watermark(mixed)

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(p), mixed)
    return str(p)

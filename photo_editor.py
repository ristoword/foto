import colorsys
from pathlib import Path
from PIL import Image, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageFont
import numpy as np


def load_image(path):
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"File non trovato: {path}")
    return Image.open(p)


def save_image(img, path, quality=95):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if img.mode in ("RGBA", "P") and p.suffix.lower() in (".jpg", ".jpeg"):
        img = img.convert("RGB")
    img.save(p, quality=quality)


def rotate(img, angle, expand=True):
    return img.rotate(angle, expand=expand, resample=Image.Resampling.BICUBIC)


def crop(img, left, top, right, bottom):
    w, h = img.size
    left = max(0, int(left * w)) if 0 <= left <= 1 else int(left)
    top = max(0, int(top * h)) if 0 <= top <= 1 else int(top)
    right = min(w, int(right * w)) if 0 < right <= 1 else int(right)
    bottom = min(h, int(bottom * h)) if 0 < bottom <= 1 else int(bottom)
    return img.crop((left, top, right, bottom))


def resize(img, width=None, height=None, keep_aspect=True):
    if not width and not height:
        return img
    w, h = img.size
    if keep_aspect:
        if width and height:
            # fit within box
            ratio = min(width / w, height / h)
            nw, nh = int(w * ratio), int(h * ratio)
        elif width:
            nh = int(h * width / w)
            nw = width
        else:
            nw = int(w * height / h)
            nh = height
    else:
        nw = width or w
        nh = height or h
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def adjust_brightness(img, factor):
    return ImageEnhance.Brightness(img).enhance(factor)


def adjust_contrast(img, factor):
    return ImageEnhance.Contrast(img).enhance(factor)


def adjust_saturation(img, factor):
    return ImageEnhance.Color(img).enhance(factor)


def apply_sharpen(img, factor=1.0):
    return ImageEnhance.Sharpness(img).enhance(1.0 + factor)


def apply_filter(img, name):
    name = name.lower()
    if name == "grayscale":
        return img.convert("L").convert(img.mode)
    if name == "sepia":
        return _sepia(img)
    if name == "blur":
        return img.filter(ImageFilter.GaussianBlur(radius=2))
    if name == "sharpen":
        return img.filter(ImageFilter.SHARPEN)
    if name == "emboss":
        return img.filter(ImageFilter.EMBOSS)
    if name == "edge":
        return img.filter(ImageFilter.FIND_EDGES)
    if name == "contour":
        return img.filter(ImageFilter.CONTOUR)
    return img


def _sepia(img):
    if img.mode != "RGB":
        img = img.convert("RGB")
    pixels = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = pixels[x, y]
            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
            pixels[x, y] = (min(255, tr), min(255, tg), min(255, tb))
    return img


def apply_curves(img, points=None):
    if img.mode != "RGB":
        img = img.convert("RGB")
    if points is None:
        points = [(0, 0), (128, 128), (255, 255)]
    lut = [0] * 256
    for i in range(256):
        # linear interpolation between points
        y = i
        for j in range(len(points) - 1):
            x0, y0 = points[j]
            x1, y1 = points[j + 1]
            if x0 <= i <= x1:
                if x1 == x0:
                    y = y0
                else:
                    t = (i - x0) / (x1 - x0)
                    y = int(y0 + t * (y1 - y0))
                break
        lut[i] = max(0, min(255, y))
    return img.point(lut * 3)


def adjust_color_balance(img, shadows=(0, 0, 0), midtones=(0, 0, 0), highlights=(0, 0, 0)):
    if img.mode != "RGB":
        img = img.convert("RGB")
    r, g, b = img.split()
    r = r.point(lambda x: max(0, min(255, x + (shadows[0] if x < 85 else midtones[0] if x < 170 else highlights[0]))))
    g = g.point(lambda x: max(0, min(255, x + (shadows[1] if x < 85 else midtones[1] if x < 170 else highlights[1]))))
    b = b.point(lambda x: max(0, min(255, x + (shadows[2] if x < 85 else midtones[2] if x < 170 else highlights[2]))))
    return Image.merge("RGB", (r, g, b))


def adjust_hsl(img, hue=0.0, saturation=1.0, lightness=0.0):
    if img.mode != "RGB":
        img = img.convert("RGB")
    import colorsys
    out = img.copy()
    pixels = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b = pixels[x, y]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            h = (h + hue / 360) % 1.0
            s = max(0, min(1, s * saturation))
            v = max(0, min(1, v + lightness))
            nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
            pixels[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255))
    return out


def adjust_vibrance(img, amount=0.0):
    if img.mode != "RGB":
        img = img.convert("RGB")
    import colorsys
    out = img.copy()
    pixels = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b = pixels[x, y]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            boost = amount * (1 - s) * 0.3
            s = max(0, min(1, s + boost))
            nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
            pixels[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255))
    return out


def apply_vignette(img, intensity=0.0):
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    overlay = Image.new("L", img.size, 255)
    for y in range(h):
        for x in range(w):
            dx = (x - w / 2) / (w / 2)
            dy = (y - h / 2) / (h / 2)
            d = min(1.0, (dx * dx + dy * dy) ** 0.5)
            val = int(255 * (1 - intensity * d))
            overlay.putpixel((x, y), val)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(w, h) / 10))
    return Image.composite(img, Image.new("RGB", img.size, (0, 0, 0)), overlay)


def apply_duotone(img, color1, color2):
    if img.mode != "RGB":
        img = img.convert("RGB")
    gray = img.convert("L")
    c1 = ImageColor.getrgb(color1) if isinstance(color1, str) else color1
    c2 = ImageColor.getrgb(color2) if isinstance(color2, str) else color2
    out = Image.new("RGB", img.size)
    pixels = out.load()
    for y in range(img.height):
        for x in range(img.width):
            t = gray.getpixel((x, y)) / 255
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            pixels[x, y] = (r, g, b)
    return out


def mirror(img, horizontal=False, vertical=False):
    if horizontal and vertical:
        return img.transpose(Image.Transpose.ROTATE_180)
    if horizontal:
        return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if vertical:
        return img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return img


def process_image(path, out, **kwargs):
    img = load_image(path)
    if "rotate" in kwargs:
        img = rotate(img, kwargs["rotate"])
    if "crop_box" in kwargs:
        img = crop(img, *kwargs["crop_box"])
    if "width" in kwargs or "height" in kwargs:
        img = resize(img, kwargs.get("width"), kwargs.get("height"), kwargs.get("keep_aspect", True))
    if "mirror_h" in kwargs and kwargs["mirror_h"]:
        img = mirror(img, horizontal=True)
    if "mirror_v" in kwargs and kwargs["mirror_v"]:
        img = mirror(img, vertical=True)
    if "curves" in kwargs:
        img = apply_curves(img, kwargs["curves"])
    if "color_balance" in kwargs:
        img = adjust_color_balance(img, *kwargs["color_balance"])
    if "hsl" in kwargs:
        img = adjust_hsl(img, *kwargs["hsl"])
    if "vibrance" in kwargs:
        img = adjust_vibrance(img, kwargs["vibrance"])
    if "vignette" in kwargs:
        img = apply_vignette(img, kwargs["vignette"])
    if "duotone" in kwargs:
        img = apply_duotone(img, *kwargs["duotone"])
    if "brightness" in kwargs:
        img = adjust_brightness(img, kwargs["brightness"])
    if "contrast" in kwargs:
        img = adjust_contrast(img, kwargs["contrast"])
    if "saturation" in kwargs:
        img = adjust_saturation(img, kwargs["saturation"])
    if "sharpen" in kwargs:
        img = apply_sharpen(img, kwargs["sharpen"])
    if "filter" in kwargs:
        img = apply_filter(img, kwargs["filter"])
    if "text" in kwargs:
        txt = kwargs["text"]
        img = add_text(
            img, txt.get("content", ""),
            position=txt.get("position", (50, 50)),
            font_size=txt.get("font_size", 40),
            color=txt.get("color", (255, 255, 255)),
            shadow=txt.get("shadow", True),
            opacity=txt.get("opacity", 255),
        )
    if "levels" in kwargs:
        lvl = kwargs["levels"]
        img = apply_levels(img, lvl.get("black", 0), lvl.get("white", 255), lvl.get("gamma", 1.0))
    if "noise_reduction" in kwargs and kwargs["noise_reduction"] > 0:
        img = reduce_noise(img, kwargs["noise_reduction"])
    if "border" in kwargs:
        brd = kwargs["border"]
        img = add_border(img, brd.get("width", 20), brd.get("color", (255, 255, 255)))
    if "auto_wb" in kwargs and kwargs["auto_wb"]:
        img = auto_white_balance(img)
    if "dodge" in kwargs:
        d = kwargs["dodge"]
        img = dodge_burn(img, d.get("amount", 0.3), mode="dodge")
    if "burn" in kwargs:
        b = kwargs["burn"]
        img = dodge_burn(img, b.get("amount", 0.3), mode="burn")
    if "gradient_map" in kwargs:
        gm = kwargs["gradient_map"]
        img = apply_gradient_map(img, gm[0], gm[1], gm.get(2, 0.5) if len(gm) > 2 else 0.5)
    save_image(img, out)


# ---------------------------------------------------------------------------
# STRUMENTI PROFESSIONALI AVANZATI
# ---------------------------------------------------------------------------

def add_text(img, text, position=(50, 50), font_size=40,
             color=(255, 255, 255), shadow=True, shadow_color=(0, 0, 0),
             opacity=255):
    """Sovrapponi testo all'immagine con ombra opzionale."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _get_font(font_size)
    if shadow:
        draw.text(
            (position[0] + 2, position[1] + 2), text, font=font,
            fill=shadow_color + (min(opacity, 200),),
        )
    draw.text(position, text, font=font, fill=color + (opacity,))
    result = Image.alpha_composite(img, overlay)
    return result.convert("RGB")


def _get_font(size):
    """Prova a caricare un font TrueType, fallback al default."""
    candidates = [
        "arial.ttf", "Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def apply_levels(img, black_point=0, white_point=255, gamma=1.0, channel="all"):
    """Regolazione livelli (punto nero, punto bianco, gamma) per canale."""
    if img.mode != "RGB":
        img = img.convert("RGB")

    def _lut(bp, wp, g):
        lut = []
        for i in range(256):
            v = max(0, min(255, (i - bp) * 255 / max(1, wp - bp)))
            v = int(255 * ((v / 255) ** (1.0 / g)))
            lut.append(max(0, min(255, v)))
        return lut

    lut = _lut(black_point, white_point, gamma)
    if channel == "all":
        return img.point(lut * 3)
    channels = list(img.split())
    ch_idx = {"r": 0, "g": 1, "b": 2}.get(channel.lower(), 0)
    channels[ch_idx] = channels[ch_idx].point(lut)
    return Image.merge("RGB", channels)


def reduce_noise(img, strength=5):
    """Riduzione rumore con filtro mediano + smoothing progressivo."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    result = img.copy()
    if strength >= 3:
        result = result.filter(ImageFilter.MedianFilter(size=3))
    passes = max(1, strength // 2)
    for _ in range(passes):
        result = result.filter(ImageFilter.SMOOTH_MORE)
    return result


def add_border(img, width=20, color=(255, 255, 255), style="solid"):
    """Aggiungi cornice/bordo attorno all'immagine."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    if style == "double":
        inner_w = max(2, width // 4)
        outer_color = color
        inner_color = tuple(max(0, c - 60) for c in color)
        s1 = (img.width + 2 * width, img.height + 2 * width)
        bordered = Image.new("RGB", s1, outer_color)
        s2 = (img.width + 2 * inner_w, img.height + 2 * inner_w)
        inner = Image.new("RGB", s2, inner_color)
        inner.paste(img, (inner_w, inner_w))
        bordered.paste(inner, (width - inner_w, width - inner_w))
        return bordered
    new_size = (img.width + 2 * width, img.height + 2 * width)
    bordered = Image.new("RGB", new_size, color)
    bordered.paste(img, (width, width))
    return bordered


def auto_white_balance(img):
    """Bilanciamento del bianco automatico (gray world assumption)."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    arr = np.array(img, dtype=np.float64)
    avg = arr.mean(axis=(0, 1))
    gray_avg = avg.mean()
    scale = gray_avg / (avg + 1e-6)
    result = np.clip(arr * scale, 0, 255).astype(np.uint8)
    return Image.fromarray(result)


def generate_histogram(img):
    """Genera un'immagine istogramma RGB."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    hist_w, hist_h = 512, 200
    hist_img = Image.new("RGB", (hist_w, hist_h), (25, 25, 30))
    draw = ImageDraw.Draw(hist_img)
    colors = [(220, 60, 60), (60, 200, 60), (60, 80, 220)]
    channel_names = ["R", "G", "B"]
    for ch_idx, (color, name) in enumerate(zip(colors, channel_names)):
        hist = img.split()[ch_idx].histogram()
        max_val = max(hist) if max(hist) > 0 else 1
        for x in range(256):
            bar_h = int(hist[x] / max_val * (hist_h - 20))
            x_pos = int(x * (hist_w - 10) / 256) + 5
            x_pos2 = int((x + 1) * (hist_w - 10) / 256) + 5
            fill = tuple(c // 2 for c in color)
            draw.rectangle([x_pos, hist_h - 10 - bar_h, x_pos2, hist_h - 10], fill=fill)
    draw.line([(5, hist_h - 10), (hist_w - 5, hist_h - 10)], fill=(100, 100, 100))
    return hist_img


def dodge_burn(img, amount=0.3, mode="dodge"):
    """Schiarisci (dodge) o scurisci (burn) globalmente."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    if mode == "dodge":
        return ImageEnhance.Brightness(img).enhance(1.0 + amount)
    return ImageEnhance.Brightness(img).enhance(1.0 - amount)


def blend_images(img1, img2, mode="normal", opacity=0.5):
    """Fondi due immagini con modalità di fusione professionali."""
    if img1.mode != "RGB":
        img1 = img1.convert("RGB")
    if img2.mode != "RGB":
        img2 = img2.convert("RGB")
    img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
    a = np.array(img1, dtype=np.float64) / 255
    b = np.array(img2, dtype=np.float64) / 255
    blend_ops = {
        "normal": lambda a, b: b,
        "multiply": lambda a, b: a * b,
        "screen": lambda a, b: 1 - (1 - a) * (1 - b),
        "overlay": lambda a, b: np.where(a < 0.5, 2 * a * b, 1 - 2 * (1 - a) * (1 - b)),
        "soft_light": lambda a, b: np.where(
            b < 0.5, 2 * a * b + a * a * (1 - 2 * b),
            2 * a * (1 - b) + np.sqrt(np.clip(a, 0, 1)) * (2 * b - 1),
        ),
        "hard_light": lambda a, b: np.where(b < 0.5, 2 * a * b, 1 - 2 * (1 - a) * (1 - b)),
        "difference": lambda a, b: np.abs(a - b),
        "exclusion": lambda a, b: a + b - 2 * a * b,
        "color_dodge": lambda a, b: np.where(b >= 1.0, 1.0, np.minimum(1.0, a / (1.0 - b + 1e-6))),
        "color_burn": lambda a, b: np.where(b <= 0.0, 0.0, np.maximum(0.0, 1 - (1 - a) / (b + 1e-6))),
    }
    op = blend_ops.get(mode, blend_ops["normal"])
    result = op(a, b)
    final = a * (1 - opacity) + result * opacity
    final = np.clip(final * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(final)


def selective_color(img, target_hue, hue_range=30, saturation_shift=0, lightness_shift=0):
    """Regola saturazione e luminosità per un intervallo di colore specifico."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    arr = np.array(img, dtype=np.float64) / 255
    target_h = (target_hue % 360) / 360.0
    range_h = hue_range / 360.0
    out = arr.copy()
    for y in range(arr.shape[0]):
        for x in range(arr.shape[1]):
            r, g, b = arr[y, x]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            dist = min(abs(h - target_h), 1 - abs(h - target_h))
            if dist <= range_h:
                factor = 1 - (dist / max(range_h, 1e-6))
                s = max(0, min(1, s + saturation_shift * factor * 0.01))
                v = max(0, min(1, v + lightness_shift * factor * 0.01))
                nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
                out[y, x] = [nr, ng, nb]
    return Image.fromarray((out * 255).astype(np.uint8))


def apply_gradient_map(img, color1, color2, opacity=0.5):
    """Applica una mappa gradiente basata sulla luminosità."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    c1 = ImageColor.getrgb(color1) if isinstance(color1, str) else color1
    c2 = ImageColor.getrgb(color2) if isinstance(color2, str) else color2
    gray = img.convert("L")
    gradient = Image.new("RGB", img.size)
    g_pixels = gradient.load()
    l_pixels = gray.load()
    for y in range(img.height):
        for x in range(img.width):
            t = l_pixels[x, y] / 255
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            g_pixels[x, y] = (r, g, b)
    return blend_images(img, gradient, "normal", opacity)


def add_watermark(img, text="© AppFoto Studio", position="bottom-right",
                  font_size=24, opacity=128):
    """Aggiungi watermark di testo semitrasparente."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _get_font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = 20
    positions = {
        "top-left": (margin, margin),
        "top-right": (img.width - tw - margin, margin),
        "bottom-left": (margin, img.height - th - margin),
        "bottom-right": (img.width - tw - margin, img.height - th - margin),
        "center": ((img.width - tw) // 2, (img.height - th) // 2),
    }
    pos = positions.get(position, positions["bottom-right"])
    draw.text((pos[0] + 1, pos[1] + 1), text, font=font, fill=(0, 0, 0, opacity // 2))
    draw.text(pos, text, font=font, fill=(255, 255, 255, opacity))
    result = Image.alpha_composite(img, overlay)
    return result.convert("RGB")


def apply_tilt_shift(img, focus_position=0.5, blur_amount=5):
    """Effetto tilt-shift (miniatura) - sfoca sopra e sotto la fascia di fuoco."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    blurred = img.filter(ImageFilter.GaussianBlur(radius=blur_amount))
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    h = img.height
    center_y = int(h * focus_position)
    band = h // 6
    for y in range(h):
        dist = abs(y - center_y)
        if dist < band:
            val = 0
        else:
            val = min(255, int((dist - band) / (h * 0.3) * 255))
        draw.line([(0, y), (img.width, y)], fill=val)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=band // 2))
    return Image.composite(blurred, img, mask)

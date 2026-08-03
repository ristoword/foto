"""AI/advanced image enhancement tools."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


# ---------------------------------------------------------------------------
# Noise reduction
# ---------------------------------------------------------------------------

def noise_reduction(img: Image.Image, strength: int = 1) -> Image.Image:
    """Median-filter based noise reduction. strength=1..3."""
    strength = max(1, min(3, strength))
    for _ in range(strength):
        img = img.filter(ImageFilter.MedianFilter(size=3))
    return img


# ---------------------------------------------------------------------------
# Auto corrections
# ---------------------------------------------------------------------------

def auto_level(img: Image.Image) -> Image.Image:
    """Per-channel histogram stretch (auto levels)."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    r, g, b = img.split()

    def stretch(ch):
        arr = np.array(ch)
        lo, hi = arr.min(), arr.max()
        if hi == lo:
            return ch
        arr = ((arr.astype(np.float32) - lo) / (hi - lo) * 255).clip(0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    return Image.merge("RGB", (stretch(r), stretch(g), stretch(b)))


def auto_white_balance(img: Image.Image) -> Image.Image:
    """Grey-world white balance."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    arr = np.array(img, dtype=np.float32)
    means = arr.mean(axis=(0, 1))
    gray = means.mean()
    scale = np.where(means > 0, gray / means, 1.0)
    arr = (arr * scale).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def auto_contrast(img: Image.Image, cutoff: float = 0.5) -> Image.Image:
    """Clip the top and bottom `cutoff`% of pixels for increased contrast."""
    from PIL import ImageOps
    return ImageOps.autocontrast(img, cutoff=cutoff)


def smart_sharpen(img: Image.Image, amount: float = 1.5, radius: int = 1, threshold: int = 3) -> Image.Image:
    """Unsharp mask sharpening (better than simple sharpen)."""
    return img.filter(ImageFilter.UnsharpMask(radius=radius, percent=int(amount * 100), threshold=threshold))


def dehaze(img: Image.Image, strength: float = 0.5) -> Image.Image:
    """Simple haze removal via dark channel prior approximation."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    arr = np.array(img, dtype=np.float32) / 255.0
    dark = arr.min(axis=2)
    kernel_size = 15
    from PIL import ImageFilter as IF
    dark_img = Image.fromarray((dark * 255).astype(np.uint8))
    dark_img = dark_img.filter(IF.MinFilter(kernel_size))
    dark = np.array(dark_img).astype(np.float32) / 255.0
    A = np.percentile(arr, 99.9, axis=(0, 1))
    t = np.clip(1 - strength * dark, 0.1, 1.0)[:, :, np.newaxis]
    result = (arr - A) / t + A
    result = np.clip(result * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(result)


def upscale(img: Image.Image, scale: float = 2.0) -> Image.Image:
    """High-quality upscaling via Lanczos resampling."""
    nw = int(img.width * scale)
    nh = int(img.height * scale)
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------------------
# Text / watermark overlay
# ---------------------------------------------------------------------------

def add_text_watermark(
    img: Image.Image,
    text: str,
    position: str = "bottom-right",
    font_size: int = 48,
    color: tuple = (255, 255, 255),
    opacity: int = 180,
    shadow: bool = True,
) -> Image.Image:
    """Overlay semi-transparent text on an image."""
    base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    font = ImageFont.load_default()
    for fp in font_paths:
        if Path(fp).exists():
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                pass
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    padding = 24
    w, h = base.size
    positions = {
        "bottom-right": (w - tw - padding, h - th - padding),
        "bottom-left": (padding, h - th - padding),
        "top-right": (w - tw - padding, padding),
        "top-left": (padding, padding),
        "center": ((w - tw) // 2, (h - th) // 2),
        "bottom-center": ((w - tw) // 2, h - th - padding),
        "top-center": ((w - tw) // 2, padding),
    }
    x, y = positions.get(position, positions["bottom-right"])
    if shadow:
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, opacity))
    draw.text((x, y), text, font=font, fill=(*color, opacity))
    return Image.alpha_composite(base, overlay).convert("RGB")


def add_image_watermark(
    img: Image.Image,
    watermark_path: str,
    position: str = "bottom-right",
    scale: float = 0.2,
    opacity: int = 150,
) -> Image.Image:
    """Overlay a watermark image (e.g. logo)."""
    base = img.convert("RGBA")
    wm = Image.open(watermark_path).convert("RGBA")
    max_w = int(base.width * scale)
    max_h = int(base.height * scale)
    wm.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    r, g, b, a = wm.split()
    a = a.point(lambda v: int(v * opacity / 255))
    wm = Image.merge("RGBA", (r, g, b, a))
    padding = 20
    w, h = base.size
    positions = {
        "bottom-right": (w - wm.width - padding, h - wm.height - padding),
        "bottom-left": (padding, h - wm.height - padding),
        "top-right": (w - wm.width - padding, padding),
        "top-left": (padding, padding),
        "center": ((w - wm.width) // 2, (h - wm.height) // 2),
    }
    x, y = positions.get(position, positions["bottom-right"])
    base.paste(wm, (x, y), wm)
    return base.convert("RGB")


# ---------------------------------------------------------------------------
# Artistic effects
# ---------------------------------------------------------------------------

def oil_paint_effect(img: Image.Image, radius: int = 2, levels: int = 8) -> Image.Image:
    """Approximate oil-paint look via median + posterize."""
    from PIL import ImageOps
    img = img.filter(ImageFilter.MedianFilter(size=radius * 2 + 1))
    return ImageOps.posterize(img, bits=max(1, 8 - levels + 1))


def pencil_sketch(img: Image.Image, blur_radius: int = 21) -> Image.Image:
    """Convert image to pencil sketch look."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    gray = img.convert("L")
    inv = gray.point(lambda x: 255 - x)
    blurred = inv.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    arr_gray = np.array(gray, dtype=np.float32)
    arr_blur = np.array(blurred, dtype=np.float32)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(arr_blur == 255, 255, np.clip(arr_gray * 255 / (255 - arr_blur), 0, 255))
    sketch = Image.fromarray(result.astype(np.uint8)).convert("RGB")
    return sketch


def vintage_effect(img: Image.Image) -> Image.Image:
    """Apply a vintage/retro colour grading."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    arr = np.array(img, dtype=np.float32)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.08, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.85, 0, 255)
    img = Image.fromarray(arr.astype(np.uint8))
    img = ImageEnhance.Color(img).enhance(0.75)
    img = ImageEnhance.Contrast(img).enhance(0.9)
    return img


def hdr_effect(img: Image.Image) -> Image.Image:
    """Simulate HDR: local contrast enhancement."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = ImageEnhance.Contrast(img).enhance(1.5)
    img = ImageEnhance.Color(img).enhance(1.4)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))
    return img


def cross_process(img: Image.Image) -> Image.Image:
    """Cross-processing effect (slide film developed as negative)."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    r, g, b = img.split()
    r = r.point(lambda v: min(255, int(v * 1.2 + 20)))
    g = g.point(lambda v: max(0, int(v * 0.85 - 10)))
    b = b.point(lambda v: min(255, int(v * 1.1 + 30)))
    return Image.merge("RGB", (r, g, b))

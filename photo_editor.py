from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter


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


def process_image(path, out, **kwargs):
    img = load_image(path)
    if "rotate" in kwargs:
        img = rotate(img, kwargs["rotate"])
    if "crop_box" in kwargs:
        img = crop(img, *kwargs["crop_box"])
    if "width" in kwargs or "height" in kwargs:
        img = resize(img, kwargs.get("width"), kwargs.get("height"), kwargs.get("keep_aspect", True))
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
    save_image(img, out)

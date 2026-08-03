import colorsys
from pathlib import Path
from PIL import Image, ImageColor, ImageEnhance, ImageFilter


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
    save_image(img, out)

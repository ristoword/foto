"""Photo collage maker — grid, horizontal, vertical, masonry, and freeform layouts."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _open(path) -> Image.Image:
    return Image.open(path).convert("RGB")


def _fit(img: Image.Image, cell_w: int, cell_h: int) -> Image.Image:
    img = img.copy()
    img.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
    return img


def _fill(img: Image.Image, cell_w: int, cell_h: int) -> Image.Image:
    """Crop-fill: scale so the image covers the cell, then centre-crop."""
    iw, ih = img.size
    ratio_w = cell_w / iw
    ratio_h = cell_h / ih
    ratio = max(ratio_w, ratio_h)
    nw = int(iw * ratio)
    nh = int(ih * ratio)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - cell_w) // 2
    top = (nh - cell_h) // 2
    return img.crop((left, top, left + cell_w, top + cell_h))


def make_grid_collage(
    image_paths,
    output_path: str,
    cols: int = 3,
    cell_width: int = 600,
    cell_height: int = 450,
    padding: int = 12,
    bg_color: tuple = (15, 15, 15),
    fit_mode: str = "fill",
    labels: bool = False,
) -> str:
    images = []
    for p in image_paths:
        try:
            images.append((Path(p).stem, _open(p)))
        except Exception:
            continue
    if not images:
        raise ValueError("Nessuna immagine valida")
    n = len(images)
    rows = (n + cols - 1) // cols
    canvas_w = cols * cell_width + (cols + 1) * padding
    canvas_h = rows * cell_height + (rows + 1) * padding
    canvas = Image.new("RGB", (canvas_w, canvas_h), bg_color)
    draw = ImageDraw.Draw(canvas)
    for i, (name, img) in enumerate(images):
        row = i // cols
        col = i % cols
        x = padding + col * (cell_width + padding)
        y = padding + row * (cell_height + padding)
        if fit_mode == "fill":
            cell_img = _fill(img, cell_width, cell_height)
        else:
            cell_img = _fit(img, cell_width, cell_height)
            bg = Image.new("RGB", (cell_width, cell_height), bg_color)
            ox = (cell_width - cell_img.width) // 2
            oy = (cell_height - cell_img.height) // 2
            bg.paste(cell_img, (ox, oy))
            cell_img = bg
        canvas.paste(cell_img, (x, y))
        if labels:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except Exception:
                font = ImageFont.load_default()
            draw.text((x + 6, y + cell_height - 22), name[:30], fill=(220, 220, 220), font=font)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, quality=96)
    return output_path


def make_strip_collage(
    image_paths,
    output_path: str,
    direction: str = "horizontal",
    size: int = 500,
    padding: int = 10,
    bg_color: tuple = (15, 15, 15),
) -> str:
    images = [_open(p) for p in image_paths if Path(p).is_file()]
    if not images:
        raise ValueError("Nessuna immagine valida")
    scaled = []
    for img in images:
        if direction == "horizontal":
            aspect = img.width / img.height
            nw = int(size * aspect)
            scaled.append(img.resize((nw, size), Image.Resampling.LANCZOS))
        else:
            aspect = img.height / img.width
            nh = int(size * aspect)
            scaled.append(img.resize((size, nh), Image.Resampling.LANCZOS))
    if direction == "horizontal":
        total_w = sum(i.width for i in scaled) + padding * (len(scaled) + 1)
        canvas = Image.new("RGB", (total_w, size + 2 * padding), bg_color)
        x = padding
        for img in scaled:
            canvas.paste(img, (x, padding))
            x += img.width + padding
    else:
        total_h = sum(i.height for i in scaled) + padding * (len(scaled) + 1)
        canvas = Image.new("RGB", (size + 2 * padding, total_h), bg_color)
        y = padding
        for img in scaled:
            canvas.paste(img, (padding, y))
            y += img.height + padding
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, quality=96)
    return output_path


def make_featured_collage(
    image_paths,
    output_path: str,
    canvas_w: int = 1920,
    canvas_h: int = 1080,
    padding: int = 10,
    bg_color: tuple = (15, 15, 15),
) -> str:
    """One large featured image on the left, up to 4 thumbnails on the right."""
    images = [_open(p) for p in image_paths if Path(p).is_file()]
    if not images:
        raise ValueError("Nessuna immagine valida")
    canvas = Image.new("RGB", (canvas_w, canvas_h), bg_color)
    main_w = canvas_w * 2 // 3
    main_img = _fill(images[0], main_w - padding * 2, canvas_h - padding * 2)
    canvas.paste(main_img, (padding, padding))
    thumb_x = main_w + padding
    rest = images[1:5]
    if rest:
        thumb_h = (canvas_h - padding * (len(rest) + 1)) // len(rest)
        thumb_w = canvas_w - thumb_x - padding
        y = padding
        for img in rest:
            t = _fill(img, thumb_w, thumb_h)
            canvas.paste(t, (thumb_x, y))
            y += thumb_h + padding
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, quality=96)
    return output_path

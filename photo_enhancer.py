import os
import argparse
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np


def correct_exposure(image: np.ndarray, gamma: float = 1.2) -> np.ndarray:
    """Apply gamma correction to brighten/darken the image."""
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)


def improve_contrast(image: np.ndarray) -> np.ndarray:
    """Apply CLAHE (contrast limited adaptive histogram equalization) in LAB color space."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)


def sharpen(image: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """Apply an unsharp mask to increase perceived sharpness."""
    blurred = cv2.GaussianBlur(image, (0, 0), 3)
    sharpened = cv2.addWeighted(image, 1 + strength, blurred, -strength, 0)
    return sharpened


def is_blurry(image: np.ndarray, threshold: float = 100.0) -> Tuple[bool, float]:
    """Return (is_blurry, variance) using the variance of Laplacian."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold, float(variance)


def enhance_image(input_path: str, output_path: str, gamma: float = 1.2, sharp_strength: float = 1.0,
                  blur_threshold: float = 100.0, report_blur: bool = True) -> Optional[dict]:
    """Load, enhance, save and return optional blur report."""
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"Cannot load image: {input_path}")

    result = image.copy()
    result = correct_exposure(result, gamma)
    result = improve_contrast(result)
    result = sharpen(result, sharp_strength)

    blurry, variance = is_blurry(image, blur_threshold)
    cv2.imwrite(output_path, result)

    if report_blur:
        print(f"{input_path}: blur variance={variance:.2f} -> {'BLURRY' if blurry else 'OK'}")
    return {"input": input_path, "output": output_path, "blur_variance": variance, "blurry": blurry}


def enhance_folder(input_folder: str, output_folder: str, gamma: float = 1.2, sharp_strength: float = 1.0,
                   blur_threshold: float = 100.0) -> None:
    """Enhance every image in *input_folder* and save to *output_folder*."""
    os.makedirs(output_folder, exist_ok=True)
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
    for path in Path(input_folder).iterdir():
        if path.suffix.lower() in exts and path.is_file():
            out = os.path.join(output_folder, path.name)
            enhance_image(str(path), out, gamma, sharp_strength, blur_threshold)


def main():
    parser = argparse.ArgumentParser(description="Enhance photos automatically.")
    sub = parser.add_subparsers(dest="command", required=True)

    single = sub.add_parser("single", help="Enhance a single photo")
    single.add_argument("input", help="Input image path")
    single.add_argument("output", help="Output image path")
    single.add_argument("--gamma", type=float, default=1.2)
    single.add_argument("--sharp", type=float, default=1.0, help="Unsharp strength")
    single.add_argument("--blur-threshold", type=float, default=100.0)

    batch = sub.add_parser("batch", help="Enhance every photo in a folder")
    batch.add_argument("input_folder")
    batch.add_argument("--output", required=True, help="Output folder")
    batch.add_argument("--gamma", type=float, default=1.2)
    batch.add_argument("--sharp", type=float, default=1.0)
    batch.add_argument("--blur-threshold", type=float, default=100.0)

    args = parser.parse_args()
    if args.command == "single":
        enhance_image(args.input, args.output, args.gamma, args.sharp, args.blur_threshold)
    else:
        enhance_folder(args.input_folder, args.output, args.gamma, args.sharp, args.blur_threshold)


if __name__ == "__main__":
    main()

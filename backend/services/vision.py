from io import BytesIO
from typing import Any, Protocol, cast

import numpy as np
from PIL import Image, ImageDraw

from backend.models.assistant import Stroke


class OcrReader(Protocol):
    def readtext(self, *args: Any, **kwargs: Any) -> Any: ...


_ocr_reader: OcrReader | None = None


def _get_ocr_reader() -> OcrReader:
    global _ocr_reader
    if _ocr_reader is None:
        try:
            import easyocr

            _ocr_reader = cast(OcrReader, easyocr.Reader(["en"], gpu=False, verbose=False))
        except Exception as exc:
            raise RuntimeError("OCR engine initialization failed") from exc
    if _ocr_reader is None:
        raise RuntimeError("OCR engine initialization failed")
    return _ocr_reader


def initialize_ocr_engine() -> None:
    _get_ocr_reader()


def rasterize_strokes_to_png(strokes: list[Stroke], width: int = 512, height: int = 512) -> bytes:
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    points_for_bounds = [
        point
        for stroke in strokes
        for point in stroke.points
    ]

    if points_for_bounds:
        min_x = min(point.x for point in points_for_bounds)
        max_x = max(point.x for point in points_for_bounds)
        min_y = min(point.y for point in points_for_bounds)
        max_y = max(point.y for point in points_for_bounds)

        span_x = max(1.0, max_x - min_x)
        span_y = max(1.0, max_y - min_y)
        margin = 36
        scale = min((width - (2 * margin)) / span_x, (height - (2 * margin)) / span_y)
        offset_x = (width - (span_x * scale)) / 2
        offset_y = (height - (span_y * scale)) / 2
        line_width = max(8, int(min(width, height) * 0.02))

        for stroke in strokes:
            if len(stroke.points) < 2:
                if len(stroke.points) == 1:
                    only = stroke.points[0]
                    x = ((only.x - min_x) * scale) + offset_x
                    y = ((only.y - min_y) * scale) + offset_y
                    r = max(2, line_width // 2)
                    draw.ellipse((x - r, y - r, x + r, y + r), fill="black")
                continue

            transformed_points = [
                (((point.x - min_x) * scale) + offset_x, ((point.y - min_y) * scale) + offset_y)
                for point in stroke.points
            ]
            draw.line(transformed_points, fill="black", width=line_width)

    with BytesIO() as output:
        image.save(output, format="PNG")
        return output.getvalue()


def extract_text_from_strokes(strokes: list[Stroke]) -> str:
    image_png = rasterize_strokes_to_png(strokes)
    return extract_text_from_png(image_png)


def _preprocess_image_variants(image_png: bytes) -> list[np.ndarray]:
    with Image.open(BytesIO(image_png)) as image:
        grayscale = image.convert("L")
        upscaled = grayscale.resize((768, 768), resample=Image.Resampling.BICUBIC)
        image_array = np.array(upscaled)

    return [
        image_array,
        np.where(image_array < 190, 0, 255).astype(np.uint8),
        np.where(image_array < 160, 0, 255).astype(np.uint8),
        np.where(image_array < 220, 0, 255).astype(np.uint8),
        255 - np.where(image_array < 180, 0, 255).astype(np.uint8),
    ]


def _run_ocr_variant(reader: OcrReader, image_variant: np.ndarray) -> list[Any]:
    raw_results = reader.readtext(
        image_variant,
        detail=1,
        paragraph=False,
        decoder="beamsearch",
        beamWidth=8,
        allowlist="0123456789+-*/=xX()[]{}.,",
        text_threshold=0.3,
        low_text=0.2,
        link_threshold=0.2,
        width_ths=0.7,
        height_ths=0.7,
        mag_ratio=1.3,
    )
    if isinstance(raw_results, list):
        return raw_results
    return []


def _extract_texts(results: list[Any]) -> list[str]:
    return [
        row[1].strip()
        for row in results
        if len(row) >= 2 and isinstance(row[1], str) and row[1].strip()
    ]


def _score_ocr_result(texts: list[str], results: list[Any]) -> tuple[str, float]:
    combined = "\n".join(texts)
    confidences = [float(row[2]) for row in results if len(row) >= 3 and isinstance(row[2], (int, float))]
    avg_confidence = float(np.mean(confidences)) if confidences else 0.0
    digit_bonus = sum(char.isdigit() for char in combined) * 0.03
    score = avg_confidence + (len(combined) * 0.002) + digit_bonus
    return combined, score


def extract_text_from_png(image_png: bytes) -> str:
    try:
        variants = _preprocess_image_variants(image_png)

        reader = _get_ocr_reader()
        best_text = ""
        best_score = -1.0

        for variant in variants:
            results = _run_ocr_variant(reader, variant)
            if not results:
                continue

            texts = _extract_texts(results)
            if not texts:
                continue

            combined, score = _score_ocr_result(texts, results)

            if score > best_score:
                best_score = score
                best_text = combined

        return best_text
    except Exception as exc:
        raise RuntimeError("OCR extraction failed") from exc

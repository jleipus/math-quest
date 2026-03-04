from io import BytesIO
from PIL import Image, ImageDraw

from backend.models.assistant import Stroke


def rasterize_strokes_to_png(strokes: list[Stroke], width: int = 512, height: int = 512) -> bytes:
    all_points = [p for s in strokes for p in s.points]
    if all_points:
        max_x = max(p.x for p in all_points)
        max_y = max(p.y for p in all_points)
        width = max(width, int(max_x) + 4)
        height = max(height, int(max_y) + 4)

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    for stroke in strokes:
        if len(stroke.points) < 2:
            continue
        points = [(point.x, point.y) for point in stroke.points]
        draw.line(points, fill="black", width=3)

    with BytesIO() as output:
        image.save(output, format="PNG")
        return output.getvalue()

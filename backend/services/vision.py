from io import BytesIO

from PIL import Image, ImageDraw

from backend.models.assistant import Stroke


def rasterize_strokes_to_png(strokes: list[Stroke], width: int = 512, height: int = 512) -> bytes:
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

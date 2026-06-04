import io
import os
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from bot.config import settings
from bot.utils.logger import logger


class PosterService:
    def __init__(self):
        self.watermark_text = settings.WATERMARK_TEXT

    def add_watermark(
        self,
        image_bytes: bytes,
        text: Optional[str] = None,
        movie_code: Optional[str] = None,
    ) -> bytes:
        """Add watermark text to poster image."""
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
            txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)

            w, h = img.size
            watermark = text or self.watermark_text
            if movie_code:
                watermark = f"{watermark} | #{movie_code}"

            # Try to load a font, fall back to default
            try:
                font_size = max(20, h // 30)
                # Windows path
                font_path = "C:\\Windows\\Fonts\\arial.ttf"
                if not os.path.exists(font_path):
                    # Linux path
                    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                else:
                    font = ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), watermark, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            margin = 15
            x = w - text_w - margin
            y = h - text_h - margin

            # Shadow
            draw.text((x + 1, y + 1), watermark, font=font, fill=(0, 0, 0, 160))
            # Main text
            draw.text((x, y), watermark, font=font, fill=(255, 255, 255, 200))

            combined = Image.alpha_composite(img, txt_layer)
            output = io.BytesIO()
            combined = combined.convert("RGB")
            combined.save(output, format="JPEG", quality=90)
            return output.getvalue()

        except Exception as e:
            logger.error(f"Watermark error: {e}")
            return image_bytes

    def resize_poster(self, image_bytes: bytes, max_size: tuple = (800, 1200)) -> bytes:
        """Resize poster to fit within max dimensions."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.thumbnail(max_size, Image.LANCZOS)
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=85)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Resize error: {e}")
            return image_bytes

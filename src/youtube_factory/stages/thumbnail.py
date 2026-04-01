"""썸네일 생성 스테이지 - Pillow로 제목 기반 썸네일."""
import logging
import textwrap

from PIL import Image, ImageDraw, ImageFont

from youtube_factory.models import PipelineContext
from youtube_factory.stages.base import Stage

log = logging.getLogger(__name__)


class ThumbnailStage(Stage):
    name = "thumbnail"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        w = self.config.get("width", 1280)
        h = self.config.get("height", 720)
        font_size = self.config.get("font_size", 72)
        font_path = self.config.get("font_path", "C:/Windows/Fonts/malgun.ttf")

        # 그라데이션 배경
        img = Image.new("RGB", (w, h))
        for y in range(h):
            r = int(20 + (y / h) * 40)
            g = int(10 + (y / h) * 20)
            b = int(80 - (y / h) * 30)
            for x in range(w):
                img.putpixel((x, y), (r, g, b))

        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype(font_path, font_size)
        except OSError:
            font = ImageFont.load_default()

        # 제목 줄바꿈 처리
        title = textwrap.fill(ctx.title, width=15)
        bbox = draw.textbbox((0, 0), title, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # 그림자 효과
        shadow_offset = 4
        draw.text(
            ((w - tw) / 2 + shadow_offset, (h - th) / 2 + shadow_offset),
            title, fill=(0, 0, 0), font=font,
        )
        # 본문
        draw.text(
            ((w - tw) / 2, (h - th) / 2),
            title, fill=(255, 255, 255), font=font,
        )

        out_path = ctx.work_dir / "thumbnail.png"
        img.save(str(out_path))
        ctx.thumbnail_path = out_path

        log.info(f"썸네일 생성 완료: {out_path}")
        return ctx

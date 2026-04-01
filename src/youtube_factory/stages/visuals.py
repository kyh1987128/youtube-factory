"""비주얼 생성 스테이지 - Gemini Imagen 또는 Pillow 플레이스홀더."""
import base64
import logging
import os
import textwrap
import time

from PIL import Image, ImageDraw, ImageFont

from youtube_factory.models import PipelineContext
from youtube_factory.stages.base import Stage

log = logging.getLogger(__name__)

# 플레이스홀더용 배경색 팔레트
COLORS = [
    (30, 30, 60), (60, 30, 30), (30, 60, 30), (50, 30, 50),
    (30, 50, 50), (60, 50, 30), (40, 30, 60), (30, 60, 50),
    (60, 30, 50), (50, 50, 30), (30, 40, 60), (60, 40, 30),
]


class VisualsStage(Stage):
    name = "visuals"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        method = self.config.get("method", "gemini")

        if method == "gemini" and os.environ.get("GOOGLE_API_KEY"):
            return self._generate_gemini(ctx)
        else:
            if method == "gemini":
                log.warning("GOOGLE_API_KEY 미설정 - 플레이스홀더로 전환")
            return self._generate_placeholder(ctx)

    def _generate_gemini(self, ctx: PipelineContext) -> PipelineContext:
        """Gemini Imagen API로 실제 이미지 생성."""
        from google import genai

        client = genai.Client()
        w = self.config.get("width", 1920)
        h = self.config.get("height", 1080)
        model = self.config.get("gemini_model", "gemini-2.0-flash-exp")
        style = self.config.get("style", "cinematic, high quality, 16:9 aspect ratio")

        for scene in ctx.scenes:
            out_path = ctx.work_dir / f"visual_{scene.index:03d}.png"

            prompt = f"{scene.visual_prompt}, {style}"
            log.info(f"장면 {scene.index} 이미지 생성 중: {scene.visual_prompt[:50]}...")

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        response_modalities=["IMAGE", "TEXT"],
                    ),
                )

                # 응답에서 이미지 추출
                image_saved = False
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                        img_bytes = part.inline_data.data
                        with open(out_path, "wb") as f:
                            f.write(img_bytes)
                        image_saved = True
                        break

                if not image_saved:
                    log.warning(f"장면 {scene.index}: 이미지 없음, 플레이스홀더 생성")
                    self._make_placeholder(out_path, scene, w, h)

                # API 속도 제한 방지
                time.sleep(self.config.get("delay_seconds", 2))

            except Exception as e:
                log.error(f"장면 {scene.index} Gemini 실패: {e}, 플레이스홀더 생성")
                self._make_placeholder(out_path, scene, w, h)

            scene.image_path = out_path

        log.info(f"비주얼 생성 완료: {len(ctx.scenes)}개 이미지")
        return ctx

    def _generate_placeholder(self, ctx: PipelineContext) -> PipelineContext:
        """Pillow로 플레이스홀더 이미지 생성."""
        w = self.config.get("width", 1920)
        h = self.config.get("height", 1080)

        for scene in ctx.scenes:
            out_path = ctx.work_dir / f"visual_{scene.index:03d}.png"
            self._make_placeholder(out_path, scene, w, h)
            scene.image_path = out_path
            log.info(f"장면 {scene.index} 플레이스홀더 생성")

        log.info(f"플레이스홀더 생성 완료: {len(ctx.scenes)}개")
        return ctx

    def _make_placeholder(self, out_path, scene, w, h):
        """단일 플레이스홀더 이미지 생성."""
        color = COLORS[scene.index % len(COLORS)]
        img = Image.new("RGB", (w, h), color=color)
        draw = ImageDraw.Draw(img)

        try:
            font_lg = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 64)
            font_sm = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 28)
        except OSError:
            font_lg = ImageFont.load_default()
            font_sm = font_lg

        draw.text((80, 80), f"Scene {scene.index + 1}", fill="white", font=font_lg)
        wrapped = textwrap.fill(scene.visual_prompt, width=60)
        draw.text((80, 200), wrapped, fill=(200, 200, 200), font=font_sm)
        img.save(str(out_path))

"""스크립트 생성 스테이지 - 장면별 나레이션 + 비주얼 프롬프트."""
import json
import logging

import anthropic

from youtube_factory.models import PipelineContext, Scene
from youtube_factory.stages.base import Stage

log = logging.getLogger(__name__)


class ScriptStage(Stage):
    name = "script"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        client = anthropic.Anthropic()
        duration = self.config.get("target_duration_seconds", 480)
        model = self.config.get("model", "claude-sonnet-4-20250514")

        log.info(f"'{ctx.title}' 스크립트 생성 중 (목표 {duration}초)...")

        resp = client.messages.create(
            model=model,
            max_tokens=self.config.get("max_tokens", 4096),
            messages=[{
                "role": "user",
                "content": (
                    f"주제: {ctx.topic}\n제목: {ctx.title}\n"
                    f"목표 영상 길이: 약 {duration}초\n\n"
                    f"유튜브 영상 스크립트를 장면별로 작성해줘.\n"
                    f"각 장면은 나레이션(한국어)과 배경 이미지 생성용 프롬프트(영어)를 포함해야 해.\n"
                    f"8~15개 장면으로 구성해줘.\n\n"
                    f"반드시 아래 JSON 배열 형식으로만 응답해:\n"
                    f'[{{"narration": "한국어 나레이션", "visual_prompt": "English image prompt, detailed, cinematic"}}]'
                ),
            }],
        )

        text = resp.content[0].text
        if "```" in text:
            text = text.split("```json")[-1].split("```")[0] if "```json" in text else text.split("```")[1].split("```")[0]
        scenes_data = json.loads(text.strip())

        ctx.scenes = [
            Scene(index=i, narration=s["narration"], visual_prompt=s["visual_prompt"])
            for i, s in enumerate(scenes_data)
        ]

        log.info(f"스크립트 생성 완료: {len(ctx.scenes)}개 장면")
        return ctx

"""스크립트 생성 스테이지 - 장면별 나레이션 + 비주얼 프롬프트."""
import json
import logging

from youtube_factory.claude_cli import ask_claude
from youtube_factory.models import PipelineContext, Scene
from youtube_factory.stages.base import Stage

log = logging.getLogger(__name__)


class ScriptStage(Stage):
    name = "script"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        duration = self.config.get("target_duration_seconds", 480)

        # 숏폼 모드는 짧은 영상
        if ctx.mode == "short-long2short":
            return self._script_long2short(ctx)

        # 변형 대본이 있으면 그걸 기반으로 장면 분할
        if ctx.adapted_script:
            return self._script_from_adapted(ctx, duration)

        # 기존 방식: 0에서 생성
        return self._script_from_scratch(ctx, duration)

    def _script_from_scratch(self, ctx: PipelineContext, duration: int) -> PipelineContext:
        """기존: 주제만으로 스크립트 생성."""
        lang = ctx.target_language or "ko"
        lang_name = {"ko": "한국어", "en": "영어", "ja": "일본어", "zh": "중국어"}.get(lang, lang)

        prompt = (
            f"주제: {ctx.topic}\n제목: {ctx.title}\n"
            f"목표 영상 길이: 약 {duration}초\n\n"
            f"유튜브 영상 스크립트를 장면별로 작성해줘.\n"
            f"각 장면은 나레이션({lang_name})과 배경 이미지 생성용 프롬프트(영어)를 포함해야 해.\n"
            f"8~15개 장면으로 구성해줘.\n\n"
            f"반드시 아래 JSON 배열 형식으로만 응답해:\n"
            f'[{{"narration": "{lang_name} 나레이션", "visual_prompt": "English image prompt, detailed, cinematic"}}]'
        )

        log.info(f"스크립트 생성 중 (목표 {duration}초)...")
        text = ask_claude(prompt, timeout=180)
        return self._parse_scenes(ctx, text)

    def _script_from_adapted(self, ctx: PipelineContext, duration: int) -> PipelineContext:
        """변형된 스크립트를 장면별로 분할."""
        lang = ctx.target_language or "ko"
        lang_name = {"ko": "한국어", "en": "영어", "ja": "일본어", "zh": "중국어"}.get(lang, lang)

        # 스크립트에서 메타데이터(제목/설명/태그) 이후 본문만 추출
        script_body = ctx.adapted_script
        if "---" in script_body:
            script_body = script_body.split("---", 1)[1]

        prompt = (
            f"아래 스크립트를 유튜브 영상의 장면별로 분할해줘.\n\n"
            f"## 스크립트\n{script_body[:6000]}\n\n"
            f"## 요구사항\n"
            f"- 8~15개 장면으로 분할\n"
            f"- 각 장면에 나레이션({lang_name})과 배경 이미지 프롬프트(영어) 포함\n"
            f"- 자연스러운 흐름 유지\n"
            f"- 목표 길이: 약 {duration}초\n\n"
            f"반드시 아래 JSON 배열 형식으로만 응답해:\n"
            f'[{{"narration": "{lang_name} 나레이션", "visual_prompt": "English image prompt, detailed, cinematic"}}]'
        )

        log.info("변형 스크립트 → 장면 분할 중...")
        text = ask_claude(prompt, timeout=180)
        return self._parse_scenes(ctx, text)

    def _script_long2short(self, ctx: PipelineContext) -> PipelineContext:
        """롱폼→숏폼: 핵심 구간별 숏폼 스크립트."""
        analysis = ctx.source_analysis

        prompt = (
            f"## 분석 결과\n{analysis[:4000]}\n\n"
            f"## 요청\n"
            f"위 분석에서 선별된 핵심 구간들을 각각 독립적인 숏폼(30~60초) 스크립트로 만들어줘.\n"
            f"각 숏폼마다:\n"
            f"- 강렬한 훅 (첫 3초)\n"
            f"- 핵심 내용 (20~50초)\n"
            f"- 짧은 클로징\n\n"
            f"반드시 아래 JSON 배열 형식으로만 응답해:\n"
            f'[{{"narration": "한국어 나레이션", "visual_prompt": "English image prompt, vertical 9:16, dynamic"}}]'
        )

        log.info("숏폼 스크립트 생성 중...")
        text = ask_claude(prompt, timeout=180)
        return self._parse_scenes(ctx, text)

    def _parse_scenes(self, ctx: PipelineContext, text: str) -> PipelineContext:
        """JSON 배열 → Scene 리스트."""
        if "```" in text:
            text = text.split("```json")[-1].split("```")[0] if "```json" in text else text.split("```")[1].split("```")[0]
        scenes_data = json.loads(text.strip())

        ctx.scenes = [
            Scene(index=i, narration=s["narration"], visual_prompt=s["visual_prompt"])
            for i, s in enumerate(scenes_data)
        ]

        log.info(f"스크립트 생성 완료: {len(ctx.scenes)}개 장면")
        return ctx

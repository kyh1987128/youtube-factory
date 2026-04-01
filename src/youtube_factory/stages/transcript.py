"""대본 추출 스테이지 - 영상 URL에서 자막/트랜스크립트 추출."""
import logging

from youtube_factory.claude_cli import ask_claude
from youtube_factory.models import PipelineContext
from youtube_factory.stages.base import Stage

log = logging.getLogger(__name__)


class TranscriptStage(Stage):
    name = "transcript"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.source_urls:
            log.warning("소스 URL 없음 - 대본 추출 건너뜀")
            return ctx

        for url in ctx.source_urls:
            log.info(f"대본 추출 중: {url}")
            transcript = self._extract(url)
            if transcript:
                ctx.source_transcripts.append(transcript)
                log.info(f"대본 추출 성공: {len(transcript)}자")
            else:
                log.warning(f"대본 추출 실패: {url}")

        log.info(f"총 {len(ctx.source_transcripts)}개 대본 추출 완료")
        return ctx

    def _extract(self, url: str) -> str:
        """Claude Code에게 영상 자막 추출 요청."""
        prompt = (
            f"이 유튜브 영상의 자막(트랜스크립트)을 추출해줘: {url}\n\n"
            f"## 방법\n"
            f"1. 해당 영상의 자막/CC를 가져와줘\n"
            f"2. 자막이 없으면 영상 내용을 웹 검색으로 찾아줘\n\n"
            f"## 출력 형식\n"
            f"자막 텍스트 전체를 그대로 출력해줘.\n"
            f"타임스탬프는 필요 없고, 대사/나레이션 텍스트만.\n"
            f"앞뒤 설명 없이 자막 내용만 출력해."
        )

        try:
            return ask_claude(prompt, timeout=120)
        except Exception as e:
            log.error(f"대본 추출 실패: {e}")
            return ""

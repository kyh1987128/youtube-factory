"""대본 분석 스테이지 - 구조, 훅, 인기 요인 분석."""
import logging

from youtube_factory.claude_cli import ask_claude
from youtube_factory.models import PipelineContext
from youtube_factory.stages.base import Stage

log = logging.getLogger(__name__)


class AnalyzeStage(Stage):
    name = "analyze"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.mode == "format-cross":
            ctx.source_analysis = self._analyze_format(ctx)
        elif ctx.mode in ("platform",):
            ctx.source_analysis = self._analyze_platform(ctx)
        elif ctx.mode in ("short-long2short", "short-short2long"):
            ctx.source_analysis = self._analyze_short(ctx)
        else:
            ctx.source_analysis = self._analyze_content(ctx)

        log.info(f"분석 완료: {len(ctx.source_analysis)}자")
        return ctx

    def _analyze_content(self, ctx: PipelineContext) -> str:
        """대본 구조 + 인기 요인 분석 (cross-lang 등)."""
        transcripts = "\n\n---\n\n".join(ctx.source_transcripts)

        prompt = (
            f"아래 유튜브 영상 대본을 분석해줘.\n\n"
            f"## 대본\n{transcripts[:8000]}\n\n"
            f"## 분석 항목\n"
            f"1. **구조**: 도입-전개-결론 흐름, 장면/섹션 구분\n"
            f"2. **훅**: 첫 30초에서 시청자를 잡는 방법\n"
            f"3. **핵심 주장/정보**: 영상의 메인 메시지\n"
            f"4. **인기 요인**: 왜 이 영상이 조회수가 높은지\n"
            f"5. **전개 기법**: 스토리텔링, 데이터 인용, 비교 등\n\n"
            f"분석 결과를 상세하게 써줘."
        )

        log.info("대본 구조 분석 중...")
        return ask_claude(prompt, timeout=120)

    def _analyze_format(self, ctx: PipelineContext) -> str:
        """형식/구조만 분석 (format-cross 모드)."""
        transcripts = "\n\n---\n\n".join(ctx.source_transcripts)

        prompt = (
            f"아래 유튜브 영상의 **형식과 구조만** 분석해줘. 내용은 분석하지 마.\n\n"
            f"## 대본\n{transcripts[:8000]}\n\n"
            f"## 분석 항목 (형식만)\n"
            f"1. **전개 패턴**: 랭킹형? 스토리형? Q&A형? 비교형? 리스트형?\n"
            f"2. **훅 방식**: 질문? 충격적 사실? 예고?\n"
            f"3. **세그먼트 구성**: 몇 개 섹션, 각 섹션 길이, 전환 방식\n"
            f"4. **클로징 방식**: CTA? 요약? 떡밥?\n"
            f"5. **편집 리듬**: 빠른 컷? 천천히 설명? 긴장감 조절?\n"
            f"6. **톤**: 진지? 유머? 교육적? 감성적?\n\n"
            f"이 형식을 다른 카테고리에 적용할 수 있도록 구조적으로 분석해줘."
        )

        log.info("영상 형식/구조 분석 중...")
        return ask_claude(prompt, timeout=120)

    def _analyze_platform(self, ctx: PipelineContext) -> str:
        """플랫폼 콘텐츠 분석 (platform 모드)."""
        prompt = (
            f"아래 콘텐츠를 분석해줘.\n\n"
            f"## 원본 콘텐츠\n{ctx.topic}\n\n"
            f"## 분석 항목\n"
            f"1. **왜 바이럴인지**: 사람들이 반응하는 포인트\n"
            f"2. **핵심 내용**: 메인 스토리/정보\n"
            f"3. **유튜브 확장 가능성**: 8~15분 롱폼으로 만들 때 추가할 수 있는 내용\n"
            f"4. **추가 조사 필요한 부분**: 배경 설명, 후속 상황 등\n\n"
            f"분석 결과를 상세하게 써줘."
        )

        log.info("플랫폼 콘텐츠 분석 중...")
        return ask_claude(prompt, timeout=120)

    def _analyze_short(self, ctx: PipelineContext) -> str:
        """숏폼/롱폼 전환 분석."""
        transcripts = "\n\n---\n\n".join(ctx.source_transcripts)

        if ctx.direction == "long2short":
            prompt = (
                f"아래 롱폼 영상 대본에서 숏폼(30~60초)으로 만들기 좋은 핵심 구간 3~5개를 선별해줘.\n\n"
                f"## 대본\n{transcripts[:8000]}\n\n"
                f"## 선별 기준\n"
                f"- 독립적으로 이해 가능한 구간\n"
                f"- 임팩트 있는 내용 (놀라운 사실, 핵심 주장)\n"
                f"- 숏폼에서 훅이 될 수 있는 부분\n\n"
                f"각 구간의 내용 요약과 왜 숏폼에 적합한지 설명해줘."
            )
        else:
            prompt = (
                f"아래 숏폼 영상들의 대본을 분석하고, 이것들을 하나의 롱폼(8~15분) 영상으로 종합할 방법을 제안해줘.\n\n"
                f"## 대본들\n{transcripts[:8000]}\n\n"
                f"## 분석\n"
                f"- 공통 주제/키워드\n"
                f"- 종합 영상의 구성 방법\n"
                f"- 추가해야 할 맥락/배경 설명\n"
            )

        log.info("숏폼/롱폼 전환 분석 중...")
        return ask_claude(prompt, timeout=120)

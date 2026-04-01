"""변형 스테이지 - 문화/언어/플랫폼/포맷 변형."""
import logging

from youtube_factory.claude_cli import ask_claude
from youtube_factory.models import PipelineContext
from youtube_factory.stages.base import Stage

log = logging.getLogger(__name__)


class AdaptStage(Stage):
    name = "adapt"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.mode in ("cross-lang", "cross-lang-reverse"):
            ctx.adapted_script = self._adapt_cross_lang(ctx)
        elif ctx.mode == "platform":
            ctx.adapted_script = self._adapt_platform(ctx)
        elif ctx.mode == "format-cross":
            ctx.adapted_script = self._adapt_format(ctx)
        elif ctx.mode == "short-short2long":
            ctx.adapted_script = self._adapt_short2long(ctx)
        else:
            log.warning(f"변형 불필요한 모드: {ctx.mode}")
            return ctx

        log.info(f"변형 완료: {len(ctx.adapted_script)}자")
        return ctx

    def _adapt_cross_lang(self, ctx: PipelineContext) -> str:
        """언어/문화 변형 (cross-lang, cross-lang-reverse)."""
        transcripts = "\n\n---\n\n".join(ctx.source_transcripts)
        analysis = ctx.source_analysis
        target = ctx.target_language

        if ctx.mode == "cross-lang":
            # 외국 → 한국
            direction_prompt = (
                f"이 영상을 한국 시청자용으로 재구성해줘.\n"
                f"- 단순 번역이 아니라, 한국 문화/맥락에 맞게 변형\n"
                f"- 한국 사례, 한국 기업, 한국 상황으로 교체\n"
                f"- 한국 시청자가 공감할 수 있는 표현 사용\n"
                f"- 한국에서 관련성 없는 내용은 대체하거나 제거\n"
            )
        else:
            # 한국 → 외국
            lang_name = {"en": "영어", "ja": "일본어", "zh": "중국어"}.get(target, target)
            direction_prompt = (
                f"이 영상을 {lang_name}권 시청자용으로 재구성해줘.\n"
                f"- 해당 문화/맥락에 맞게 변형\n"
                f"- 한국 특유의 레퍼런스는 해외 시청자가 이해할 수 있게 설명 추가 또는 교체\n"
                f"- 해당 언어로 자연스러운 스크립트 작성\n"
            )

        prompt = (
            f"## 원본 대본\n{transcripts[:6000]}\n\n"
            f"## 분석 결과\n{analysis[:3000]}\n\n"
            f"## 변형 요청\n"
            f"{direction_prompt}\n"
            f"## 출력\n"
            f"변형된 전체 스크립트를 써줘. 장면 구분 없이 하나의 흐름으로.\n"
            f"동시에 영상 제목, 설명, 태그도 제안해줘.\n\n"
            f"형식:\n"
            f"제목: ...\n"
            f"설명: ...\n"
            f"태그: 태그1, 태그2, ...\n"
            f"---\n"
            f"(스크립트 본문)"
        )

        log.info(f"언어/문화 변형 중 ({ctx.mode})...")
        result = ask_claude(prompt, timeout=180)
        self._parse_metadata(ctx, result)
        return result

    def _adapt_platform(self, ctx: PipelineContext) -> str:
        """플랫폼 콘텐츠 → 유튜브 롱폼 변형."""
        analysis = ctx.source_analysis

        prompt = (
            f"## 원본 콘텐츠 분석\n{analysis[:4000]}\n\n"
            f"## 변형 요청\n"
            f"이 콘텐츠를 유튜브 8~15분 롱폼 영상 스크립트로 확장해줘.\n"
            f"- 배경 설명 추가 (시청자가 맥락을 이해할 수 있게)\n"
            f"- 분석/시사점 추가 (단순 전달이 아닌 인사이트)\n"
            f"- 강력한 훅으로 시작\n"
            f"- 시청자 참여 유도 (질문, 댓글 요청)\n\n"
            f"## 출력\n"
            f"제목: ...\n"
            f"설명: ...\n"
            f"태그: 태그1, 태그2, ...\n"
            f"---\n"
            f"(스크립트 본문)"
        )

        log.info("플랫폼→유튜브 변형 중...")
        result = ask_claude(prompt, timeout=180)
        self._parse_metadata(ctx, result)
        return result

    def _adapt_format(self, ctx: PipelineContext) -> str:
        """포맷 크로스 - 형식을 다른 카테고리에 적용."""
        analysis = ctx.source_analysis
        target_cat = ctx.target_category

        prompt = (
            f"## 원본 영상의 형식 분석\n{analysis[:4000]}\n\n"
            f"## 변형 요청\n"
            f"위 영상의 형식/구조를 '{target_cat}' 카테고리에 적용해서 새 스크립트를 써줘.\n\n"
            f"- 형식(전개 패턴, 훅, 세그먼트 구성, 톤)은 원본을 따름\n"
            f"- 내용은 '{target_cat}' 관련으로 완전히 새로 작성\n"
            f"- 한국 시청자 대상\n\n"
            f"## 출력\n"
            f"제목: ...\n"
            f"설명: ...\n"
            f"태그: 태그1, 태그2, ...\n"
            f"---\n"
            f"(스크립트 본문)"
        )

        log.info(f"포맷 크로스 변형 중 (→ {target_cat})...")
        result = ask_claude(prompt, timeout=180)
        self._parse_metadata(ctx, result)
        return result

    def _adapt_short2long(self, ctx: PipelineContext) -> str:
        """숏폼 여러 개 → 롱폼 종합."""
        analysis = ctx.source_analysis
        transcripts = "\n\n---\n\n".join(ctx.source_transcripts)

        prompt = (
            f"## 숏폼 대본들\n{transcripts[:6000]}\n\n"
            f"## 분석 결과\n{analysis[:3000]}\n\n"
            f"## 변형 요청\n"
            f"위 숏폼 영상들을 하나의 8~15분 롱폼 종합 영상으로 만들어줘.\n"
            f"- 공통 주제로 엮어서 자연스러운 흐름\n"
            f"- 각 숏폼의 핵심을 살리되 맥락/배경 추가\n"
            f"- 종합 분석/시사점으로 마무리\n\n"
            f"## 출력\n"
            f"제목: ...\n"
            f"설명: ...\n"
            f"태그: 태그1, 태그2, ...\n"
            f"---\n"
            f"(스크립트 본문)"
        )

        log.info("숏폼→롱폼 종합 변형 중...")
        result = ask_claude(prompt, timeout=180)
        self._parse_metadata(ctx, result)
        return result

    def _parse_metadata(self, ctx: PipelineContext, text: str):
        """변형 결과에서 제목/설명/태그를 파싱하여 ctx에 저장."""
        lines = text.split("\n")
        for line in lines:
            if line.startswith("제목:"):
                ctx.title = line.replace("제목:", "").strip()
            elif line.startswith("설명:"):
                ctx.description = line.replace("설명:", "").strip()
            elif line.startswith("태그:"):
                ctx.tags = [t.strip() for t in line.replace("태그:", "").split(",") if t.strip()]
            elif line.strip() == "---":
                break

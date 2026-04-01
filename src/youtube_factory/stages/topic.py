"""주제 리서치 스테이지 - 모드별 다른 접근."""
import json
import logging

from youtube_factory.claude_cli import ask_claude
from youtube_factory.models import PipelineContext

log = logging.getLogger(__name__)


class TopicStage:
    name = "topic"

    def __init__(self, config: dict):
        self.config = config

    def run(self, ctx: PipelineContext) -> PipelineContext:
        mode = ctx.mode

        if mode == "trending":
            return self._trending(ctx)
        elif mode in ("cross-lang", "cross-lang-reverse"):
            return self._cross_lang_research(ctx)
        elif mode == "platform":
            return self._platform_research(ctx)
        elif mode == "format-cross":
            return self._format_cross_topic(ctx)
        elif mode == "short-short2long":
            return self._short2long_topic(ctx)
        else:
            return self._trending(ctx)

    def _trending(self, ctx: PipelineContext) -> PipelineContext:
        """기존: 트렌딩 기반 신규 주제 선정."""
        category = self.config.get("category", "tech")
        language = self.config.get("language", "ko")
        preferred = self.config.get("preferred_categories", ["tech", "finance", "education"])

        prompt = (
            f"유튜브 영상 주제를 선정하기 위해 현재 트렌딩을 조사해줘.\n\n"
            f"## 조사 방법\n"
            f"1. 구글에서 한국/해외 실시간 트렌딩 키워드 검색\n"
            f"2. 유튜브에서 현재 인기 급상승 영상 확인\n"
            f"3. 네이버에서 실시간 검색어/뉴스 트렌드 확인\n"
            f"4. 레딧에서 해외 핫 토픽 확인\n\n"
            f"## 조건\n"
            f"- 선호 카테고리: {', '.join(preferred)}\n"
            f"- 영상 언어: {language}\n"
            f"- 여러 플랫폼에서 동시에 화제인 주제 우선\n"
            f"- 클릭률이 높을 주제\n\n"
            f"반드시 아래 JSON 형식으로만 응답해:\n"
            f'{{"topic": "주제 설명", "title": "영상 제목", '
            f'"description": "영상 설명 (2-3문장)", "tags": ["태그1", "태그2", "태그3"], '
            f'"reasoning": "선택 이유"}}'
        )

        log.info("트렌딩 조사 중...")
        text = ask_claude(prompt, timeout=180)
        return self._parse_topic_json(ctx, text)

    def _cross_lang_research(self, ctx: PipelineContext) -> PipelineContext:
        """외국/한국 인기 영상 탐색 (URL 없을 때 자동 탐색)."""
        if ctx.source_urls:
            # URL이 이미 있으면 그걸 사용
            ctx.topic = f"소스 영상 기반 ({ctx.source_urls[0]})"
            ctx.title = "소스 영상 변형"
            return ctx

        category = self.config.get("category", "tech")

        if ctx.mode == "cross-lang":
            # 해외 인기 영상 자동 탐색
            prompt = (
                f"유튜브에서 '{category}' 카테고리의 **영어권 인기 영상** 중,\n"
                f"한국 시청자용으로 변형하기 좋은 영상을 찾아줘.\n\n"
                f"## 조건\n"
                f"- 최근 1개월 이내 업로드\n"
                f"- 조회수 10만 이상\n"
                f"- 한국에 아직 유사 콘텐츠가 없거나 적은 주제\n"
                f"- 문화 차이 없이 변형 가능한 주제\n\n"
                f"반드시 아래 JSON 형식으로만 응답해:\n"
                f'{{"topic": "영상 주제", "title": "원본 영상 제목", '
                f'"description": "영상 내용 요약", "tags": ["태그1", "태그2"], '
                f'"source_url": "유튜브 URL", "reasoning": "이 영상을 선택한 이유"}}'
            )
        else:
            # 한국 인기 영상 자동 탐색
            prompt = (
                f"유튜브에서 '{category}' 카테고리의 **한국어 인기 영상** 중,\n"
                f"해외 시청자용으로 변형하기 좋은 영상을 찾아줘.\n\n"
                f"## 조건\n"
                f"- 최근 1개월 이내\n"
                f"- 조회수 높은 영상\n"
                f"- 해외에서도 관심 가질 만한 주제 (K-문화, 한국 테크 등)\n\n"
                f"반드시 아래 JSON 형식으로만 응답해:\n"
                f'{{"topic": "영상 주제", "title": "원본 영상 제목", '
                f'"description": "영상 내용 요약", "tags": ["태그1", "태그2"], '
                f'"source_url": "유튜브 URL", "reasoning": "이 영상을 선택한 이유"}}'
            )

        log.info(f"인기 영상 자동 탐색 중 ({ctx.mode})...")
        text = ask_claude(prompt, timeout=180)
        data = self._extract_json(text)

        ctx.topic = data.get("topic", "")
        ctx.title = data.get("title", "")
        ctx.description = data.get("description", "")
        ctx.tags = data.get("tags", [])

        # 자동 탐색된 URL 추가
        if "source_url" in data and data["source_url"]:
            ctx.source_urls.append(data["source_url"])
            log.info(f"소스 영상: {data['source_url']}")

        log.info(f"주제: {ctx.title}")
        return ctx

    def _platform_research(self, ctx: PipelineContext) -> PipelineContext:
        """다른 플랫폼 바이럴 콘텐츠 탐색."""
        platform = ctx.platform or "reddit"
        category = self.config.get("category", "tech")

        platform_desc = {
            "reddit": "레딧에서 최근 핫한 게시물 (r/all, r/technology 등)",
            "tiktok": "틱톡에서 바이럴 되고 있는 트렌드/챌린지",
            "news": "국내외 화제 뉴스 기사",
        }.get(platform, f"{platform}에서 인기 콘텐츠")

        prompt = (
            f"{platform_desc}을 검색해서, 유튜브 롱폼 영상으로 만들기 좋은 콘텐츠를 찾아줘.\n\n"
            f"## 조건\n"
            f"- 카테고리: {category}\n"
            f"- 반응도(업보트/좋아요/댓글)가 높은 콘텐츠\n"
            f"- 유튜브 8~15분 영상으로 확장 가능한 것\n"
            f"- 한국 시청자 관점에서 흥미로운 것\n\n"
            f"반드시 아래 JSON 형식으로만 응답해:\n"
            f'{{"topic": "콘텐츠 요약", "title": "유튜브 영상 제목 (한국어)", '
            f'"description": "영상 설명", "tags": ["태그1", "태그2"], '
            f'"source_url": "원본 URL (있으면)", "reasoning": "이 콘텐츠를 선택한 이유"}}'
        )

        log.info(f"{platform} 바이럴 탐색 중...")
        text = ask_claude(prompt, timeout=180)
        data = self._extract_json(text)

        ctx.topic = data.get("topic", "")
        ctx.title = data.get("title", "")
        ctx.description = data.get("description", "")
        ctx.tags = data.get("tags", [])

        if "source_url" in data and data["source_url"]:
            ctx.source_urls.append(data["source_url"])

        log.info(f"주제: {ctx.title}")
        return ctx

    def _format_cross_topic(self, ctx: PipelineContext) -> PipelineContext:
        """포맷 크로스: 타겟 카테고리에서 구체적 주제 선정."""
        target_cat = ctx.target_category
        analysis = ctx.source_analysis

        prompt = (
            f"## 원본 영상 형식 분석\n{analysis[:3000]}\n\n"
            f"## 요청\n"
            f"위 형식을 '{target_cat}' 카테고리에 적용할 구체적인 주제를 선정해줘.\n"
            f"- 현재 트렌딩이거나 관심도가 높은 주제\n"
            f"- 위 형식과 잘 맞는 주제\n\n"
            f"반드시 아래 JSON 형식으로만 응답해:\n"
            f'{{"topic": "주제 설명", "title": "영상 제목", '
            f'"description": "영상 설명", "tags": ["태그1", "태그2"], '
            f'"reasoning": "이 주제가 해당 형식과 맞는 이유"}}'
        )

        log.info(f"포맷 크로스 주제 선정 중 (→ {target_cat})...")
        text = ask_claude(prompt, timeout=120)
        return self._parse_topic_json(ctx, text)

    def _short2long_topic(self, ctx: PipelineContext) -> PipelineContext:
        """숏폼→롱폼: 숏폼 URL 없으면 자동 수집."""
        if ctx.source_urls:
            ctx.topic = "숏폼 종합"
            ctx.title = "숏폼 종합 영상"
            return ctx

        category = self.config.get("category", "tech")

        prompt = (
            f"'{category}' 카테고리에서 최근 인기 있는 유튜브 쇼츠/숏폼 영상들을 찾아줘.\n"
            f"같은 주제의 영상 3~5개를 찾아서 URL과 내용을 알려줘.\n\n"
            f"반드시 아래 JSON 형식으로만 응답해:\n"
            f'{{"topic": "공통 주제", "title": "종합 영상 제목", '
            f'"description": "종합 영상 설명", "tags": ["태그1", "태그2"], '
            f'"source_urls": ["URL1", "URL2", "URL3"]}}'
        )

        log.info("숏폼 영상 자동 수집 중...")
        text = ask_claude(prompt, timeout=180)
        data = self._extract_json(text)

        ctx.topic = data.get("topic", "")
        ctx.title = data.get("title", "")
        ctx.description = data.get("description", "")
        ctx.tags = data.get("tags", [])
        if "source_urls" in data:
            ctx.source_urls.extend(data["source_urls"])

        return ctx

    def _parse_topic_json(self, ctx: PipelineContext, text: str) -> PipelineContext:
        """JSON 응답 파싱하여 ctx에 저장."""
        data = self._extract_json(text)
        ctx.topic = data.get("topic", "")
        ctx.title = data.get("title", "")
        ctx.description = data.get("description", "")
        ctx.tags = data.get("tags", [])
        log.info(f"주제 선정: {ctx.title}")
        log.info(f"선정 이유: {data.get('reasoning', '')}")
        return ctx

    def _extract_json(self, text: str) -> dict:
        """텍스트에서 JSON 추출."""
        if "```" in text:
            text = text.split("```json")[-1].split("```")[0] if "```json" in text else text.split("```")[1].split("```")[0]
        return json.loads(text.strip())

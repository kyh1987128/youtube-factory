"""주제 리서치 스테이지 - 멀티소스 트렌딩 데이터 수집 + Claude 분석."""
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from youtube_factory.claude_cli import ask_claude
from youtube_factory.collectors import BaseCollector
from youtube_factory.collectors.google_trends import GoogleTrendsCollector
from youtube_factory.collectors.naver_trends import NaverTrendsCollector
from youtube_factory.collectors.reddit_trends import RedditTrendsCollector
from youtube_factory.collectors.youtube_trending import YouTubeTrendingCollector
from youtube_factory.models import PipelineContext, TrendingItem
from youtube_factory.scoring import rank_topics

log = logging.getLogger(__name__)

COLLECTOR_REGISTRY: dict[str, type[BaseCollector]] = {
    "youtube_trending": YouTubeTrendingCollector,
    "google_trends": GoogleTrendsCollector,
    "naver_trends": NaverTrendsCollector,
    "reddit_trends": RedditTrendsCollector,
}


def _parse_json(text: str) -> dict | list:
    """Claude 응답에서 JSON 추출."""
    if "```" in text:
        text = text.split("```json")[-1].split("```")[0] if "```json" in text else text.split("```")[1].split("```")[0]
    return json.loads(text.strip())


class TopicStage:
    name = "topic"

    def __init__(self, config: dict):
        self.config = config

    def run(self, ctx: PipelineContext) -> PipelineContext:
        # 1. 데이터 수집
        all_items = self._collect_all()

        # 2. 수집 실패 시 Claude 단독 폴백
        if not all_items:
            log.warning("모든 수집기 실패 - Claude 단독 모드로 전환")
            return self._fallback_claude_only(ctx)

        # 3. 스코어링
        preferred = self.config.get("preferred_categories", [])
        max_candidates = self.config.get("max_candidates", 10)
        top_topics = rank_topics(all_items, preferred, max_candidates)

        log.info(f"수집 완료: {len(all_items)}개 항목 → 상위 {len(top_topics)}개 후보")

        # 4. Claude 최종 선정
        return self._select_with_claude(ctx, top_topics)

    def _collect_all(self) -> list[TrendingItem]:
        """모든 활성 수집기를 병렬 실행."""
        collectors_config = self.config.get("collectors", {})
        timeout = self.config.get("collector_timeout_seconds", 30)

        active: list[BaseCollector] = []
        for name, cls in COLLECTOR_REGISTRY.items():
            col_cfg = collectors_config.get(name, {})
            if col_cfg.get("enabled", True):
                active.append(cls(col_cfg))

        if not active:
            log.warning("활성화된 수집기 없음")
            return []

        log.info(f"수집기 {len(active)}개 병렬 실행: {[c.name for c in active]}")

        all_items: list[TrendingItem] = []

        with ThreadPoolExecutor(max_workers=len(active)) as pool:
            futures = {pool.submit(c.collect): c for c in active}

            for future in as_completed(futures, timeout=timeout + 5):
                collector = futures[future]
                try:
                    items = future.result(timeout=timeout)
                    all_items.extend(items)
                    log.info(f"[{collector.name}] {len(items)}개 수집 성공")
                except Exception as e:
                    log.error(f"[{collector.name}] 수집 실패: {e}")

        return all_items

    def _select_with_claude(self, ctx: PipelineContext, top_topics) -> PipelineContext:
        """Claude에게 상위 후보를 보내고 최적 주제 선정."""
        category = self.config.get("category", "tech")
        language = self.config.get("language", "ko")

        candidates = []
        for t in top_topics:
            candidates.append({
                "title": t.title,
                "category": t.category,
                "score": t.final_score,
                "sources": t.sources,
                "source_count": t.source_count,
                "sample_data": [
                    {"title": it.title, "source": it.source,
                     "views": it.view_count, "likes": it.like_count,
                     "comments": it.comment_count, "velocity": round(it.trend_velocity, 2)}
                    for it in t.items[:3]
                ],
            })

        prompt = (
            f"아래는 현재 국내외 트렌딩 데이터를 수집하고 스코어링한 상위 주제 후보들이야.\n\n"
            f"## 후보 목록\n```json\n{json.dumps(candidates, ensure_ascii=False, indent=2)}\n```\n\n"
            f"## 조건\n"
            f"- 선호 카테고리: {category}\n"
            f"- 영상 언어: {language}\n"
            f"- 대상: 한국 유튜브 시청자\n"
            f"- 조회수/반응도가 높고, 여러 소스에서 동시에 뜨는 주제 우선\n"
            f"- 영상으로 만들었을 때 클릭률이 높을 만한 주제 선택\n\n"
            f"## 요청\n"
            f"가장 좋은 주제 1개를 골라서 유튜브 영상용으로 다듬어줘.\n"
            f"반드시 아래 JSON 형식으로만 응답해:\n"
            f'{{"topic": "선정 주제 설명", "title": "유튜브 영상 제목 (클릭 유도)", '
            f'"description": "영상 설명 (2-3문장)", "tags": ["태그1", "태그2", ...], '
            f'"reasoning": "이 주제를 선택한 이유"}}'
        )

        log.info("Claude에게 주제 선정 요청 중...")
        text = ask_claude(prompt, timeout=120)
        data = _parse_json(text)

        ctx.topic = data["topic"]
        ctx.title = data["title"]
        ctx.description = data["description"]
        ctx.tags = data["tags"]

        log.info(f"주제 선정: {ctx.title}")
        log.info(f"선정 이유: {data.get('reasoning', '')}")
        return ctx

    def _fallback_claude_only(self, ctx: PipelineContext) -> PipelineContext:
        """수집 실패 시 Claude 단독으로 주제 생성."""
        category = self.config.get("category", "tech")
        language = self.config.get("language", "ko")

        prompt = (
            f"유튜브 영상으로 만들기 좋은 주제를 하나 제안해줘.\n"
            f"카테고리: {category}\n언어: {language}\n\n"
            f"반드시 아래 JSON 형식으로만 응답해:\n"
            f'{{"topic": "주제 설명", "title": "영상 제목", '
            f'"description": "영상 설명 (2-3문장)", "tags": ["태그1", "태그2", "태그3"]}}'
        )

        log.info("Claude에게 주제 생성 요청 중...")
        text = ask_claude(prompt, timeout=120)
        data = _parse_json(text)

        ctx.topic = data["topic"]
        ctx.title = data["title"]
        ctx.description = data["description"]
        ctx.tags = data["tags"]

        log.info(f"주제 선정 (폴백): {ctx.title}")
        return ctx

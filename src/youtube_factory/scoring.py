"""주제 스코어링 및 랭킹 - 수집된 트렌딩 데이터 분석."""
import logging
from collections import defaultdict
from difflib import SequenceMatcher

from youtube_factory.models import ScoredTopic, TrendingItem

log = logging.getLogger(__name__)


def _normalize_scores(items: list[TrendingItem]) -> None:
    """소스별 점수를 0~100으로 정규화 (in-place)."""
    by_source: dict[str, list[TrendingItem]] = defaultdict(list)
    for item in items:
        by_source[item.source].append(item)

    for source, source_items in by_source.items():
        scores = [it.score_raw for it in source_items]
        min_s, max_s = min(scores), max(scores)
        spread = max_s - min_s if max_s > min_s else 1
        for it in source_items:
            it.score_raw = (it.score_raw - min_s) / spread * 100


def _similarity(a: str, b: str) -> float:
    """두 문자열의 유사도 (0~1)."""
    a_tokens = set(a.lower().split())
    b_tokens = set(b.lower().split())
    if not a_tokens or not b_tokens:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    overlap = len(a_tokens & b_tokens)
    return overlap / min(len(a_tokens), len(b_tokens))


def _cluster_topics(items: list[TrendingItem], threshold: float = 0.35) -> list[list[TrendingItem]]:
    """유사한 주제끼리 클러스터링."""
    clusters: list[list[TrendingItem]] = []
    used = set()

    # 점수 높은 순으로 정렬하여 대표 주제가 클러스터 중심이 되도록
    sorted_items = sorted(items, key=lambda x: x.score_raw, reverse=True)

    for i, item in enumerate(sorted_items):
        if i in used:
            continue

        cluster = [item]
        used.add(i)

        for j, other in enumerate(sorted_items):
            if j in used:
                continue
            if _similarity(item.title, other.title) >= threshold:
                cluster.append(other)
                used.add(j)

        clusters.append(cluster)

    return clusters


def rank_topics(
    items: list[TrendingItem],
    preferred_categories: list[str] | None = None,
    max_results: int = 10,
) -> list[ScoredTopic]:
    """트렌딩 아이템을 스코어링하여 상위 주제 반환.

    스코어링 공식:
    - 정규화 점수 (0~100)
    - 크로스소스 보너스: 2개 소스 = 1.3x, 3개 = 1.6x, 4개 = 1.9x
    - 카테고리 선호도: 선호 카테고리 1.5x
    - 트렌드 속도: velocity 반영
    """
    if not items:
        return []

    # 1. 소스별 점수 정규화
    _normalize_scores(items)

    # 2. 유사 주제 클러스터링
    clusters = _cluster_topics(items)

    # 3. 클러스터별 점수 계산
    scored: list[ScoredTopic] = []

    for cluster in clusters:
        # 대표 제목: 가장 높은 점수의 아이템
        best = max(cluster, key=lambda x: x.score_raw)
        sources = list({it.source for it in cluster})
        source_count = len(sources)

        # 클러스터 평균 점수
        avg_score = sum(it.score_raw for it in cluster) / len(cluster)

        # 크로스소스 보너스
        cross_multiplier = 1 + 0.3 * (source_count - 1)

        # 카테고리 선호도
        category = best.category or _most_common_category(cluster)
        cat_multiplier = 1.5 if preferred_categories and category in preferred_categories else 1.0

        # 트렌드 속도 보너스
        max_velocity = max(it.trend_velocity for it in cluster)
        velocity_bonus = 1 + 0.2 * min(max_velocity, 5)  # 최대 2x

        final_score = avg_score * cross_multiplier * cat_multiplier * velocity_bonus

        scored.append(ScoredTopic(
            title=best.title,
            category=category,
            final_score=round(final_score, 2),
            sources=sources,
            source_count=source_count,
            items=cluster,
        ))

    # 4. 정렬 및 반환
    scored.sort(key=lambda x: x.final_score, reverse=True)
    log.info(f"스코어링 완료: {len(scored)}개 주제 중 상위 {max_results}개 선정")
    return scored[:max_results]


def _most_common_category(items: list[TrendingItem]) -> str:
    """클러스터 내 가장 빈번한 카테고리."""
    counts: dict[str, int] = defaultdict(int)
    for it in items:
        if it.category:
            counts[it.category] += 1
    return max(counts, key=counts.get, default="general") if counts else "general"

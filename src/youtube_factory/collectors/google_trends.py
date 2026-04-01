"""Google Trends 수집기 - pytrends 사용."""
import logging

from youtube_factory.collectors import BaseCollector
from youtube_factory.models import TrendingItem

log = logging.getLogger(__name__)


class GoogleTrendsCollector(BaseCollector):
    name = "google_trends"

    def collect(self) -> list[TrendingItem]:
        try:
            from pytrends.request import TrendReq
        except ImportError:
            log.warning("pytrends 미설치 - Google Trends 수집 건너뜀")
            return []

        regions = self.config.get("regions", ["south_korea", "united_states"])
        region_codes = {"south_korea": "KR", "united_states": "US", "japan": "JP"}
        items = []

        pytrends = TrendReq(hl="ko")

        for region in regions:
            try:
                # 실시간 트렌딩 검색어
                trending = pytrends.trending_searches(pn=region)
                queries = trending[0].tolist() if not trending.empty else []

                for rank, query in enumerate(queries[:30]):
                    # 순위 기반 점수 (1위 = 100, 30위 ≈ 3)
                    score = max(1, 100 - rank * 3.3)

                    items.append(TrendingItem(
                        title=query,
                        source="google_trends",
                        category="",  # 스코어링에서 Claude가 분류
                        score_raw=score,
                        region=region_codes.get(region, region.upper()),
                        metadata={"rank": rank + 1, "region_name": region},
                    ))

                log.info(f"Google Trends {region}: {len(queries[:30])}개 수집")

            except Exception as e:
                log.error(f"Google Trends {region} 수집 실패: {e}")

        # 관심도 상승 키워드 수집 (선택적)
        try:
            rising = self._get_rising_queries(pytrends)
            items.extend(rising)
        except Exception as e:
            log.debug(f"상승 키워드 수집 실패 (무시): {e}")

        return items

    def _get_rising_queries(self, pytrends) -> list[TrendingItem]:
        """카테고리별 급상승 키워드 수집."""
        # YouTube 관련 카테고리 ID: 3=비즈니스, 5=엔터, 8=게임, 13=쇼핑, 16=뉴스
        categories = {"tech": 5, "finance": 3, "entertainment": 8}
        items = []

        for cat_name, cat_id in categories.items():
            try:
                pytrends.build_payload(
                    kw_list=[""],
                    cat=cat_id,
                    timeframe="now 1-d",
                    geo="KR",
                )
                related = pytrends.related_queries()
                for kw, data in related.items():
                    rising = data.get("rising")
                    if rising is not None and not rising.empty:
                        for _, row in rising.head(5).iterrows():
                            items.append(TrendingItem(
                                title=row["query"],
                                source="google_trends",
                                category=cat_name,
                                score_raw=float(row.get("value", 50)),
                                trend_velocity=float(row.get("value", 0)) / 100,
                                region="KR",
                                metadata={"type": "rising", "category_id": cat_id},
                            ))
            except Exception:
                pass

        return items

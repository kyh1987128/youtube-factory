"""네이버 트렌드 수집기 - Naver DataLab / 검색 API."""
import logging
import os
from datetime import datetime, timedelta

import requests

from youtube_factory.collectors import BaseCollector
from youtube_factory.models import TrendingItem

log = logging.getLogger(__name__)

DATALAB_URL = "https://openapi.naver.com/v1/datalab/search"
SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"

# 카테고리별 시드 키워드 (네이버 DataLab 검색용)
SEED_KEYWORDS = {
    "tech": ["AI 인공지능", "챗GPT", "반도체", "스마트폰", "로봇"],
    "finance": ["주식 전망", "비트코인", "부동산", "금리 인상", "환율"],
    "health": ["다이어트", "운동 루틴", "건강 식단", "수면", "스트레스"],
    "education": ["코딩 교육", "자격증", "취업 준비", "영어 공부", "대학입시"],
    "entertainment": ["넷플릭스", "인기 드라마", "K-POP", "게임 신작", "영화 추천"],
    "lifestyle": ["맛집 추천", "국내 여행", "인테리어", "요리 레시피", "카페"],
}


class NaverTrendsCollector(BaseCollector):
    name = "naver_trends"

    def collect(self) -> list[TrendingItem]:
        client_id = os.environ.get("NAVER_CLIENT_ID")
        client_secret = os.environ.get("NAVER_CLIENT_SECRET")

        if not client_id or not client_secret:
            log.warning("NAVER_CLIENT_ID/SECRET 미설정 - 네이버 수집 건너뜀")
            return []

        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }

        items = []

        # 1. DataLab 검색 트렌드
        items.extend(self._collect_datalab(headers))

        # 2. 뉴스 검색으로 화제 키워드
        items.extend(self._collect_news_trends(headers))

        return items

    def _collect_datalab(self, headers: dict) -> list[TrendingItem]:
        """네이버 DataLab으로 카테고리별 검색 트렌드 수집."""
        items = []
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        for category, keywords in SEED_KEYWORDS.items():
            try:
                body = {
                    "startDate": start_date,
                    "endDate": end_date,
                    "timeUnit": "date",
                    "keywordGroups": [
                        {"groupName": kw, "keywords": [kw]}
                        for kw in keywords
                    ],
                }

                resp = requests.post(DATALAB_URL, json=body, headers=headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()

                for group in data.get("results", []):
                    name = group["title"]
                    ratios = [p["ratio"] for p in group.get("data", [])]
                    if not ratios:
                        continue

                    latest = ratios[-1]
                    avg = sum(ratios) / len(ratios)
                    # 최근 값이 평균보다 높으면 상승 트렌드
                    velocity = (latest - avg) / max(avg, 1)

                    items.append(TrendingItem(
                        title=name,
                        source="naver",
                        category=category,
                        score_raw=latest,
                        trend_velocity=velocity,
                        region="KR",
                        metadata={"avg_ratio": avg, "latest_ratio": latest},
                    ))

                log.info(f"네이버 DataLab {category}: {len(keywords)}개 키워드 분석")

            except Exception as e:
                log.error(f"네이버 DataLab {category} 실패: {e}")

        return items

    def _collect_news_trends(self, headers: dict) -> list[TrendingItem]:
        """네이버 뉴스 검색으로 화제 키워드 수집."""
        items = []
        hot_queries = ["화제", "논란", "인기", "트렌드", "핫이슈"]

        for query in hot_queries:
            try:
                resp = requests.get(
                    SEARCH_URL,
                    params={"query": query, "display": 10, "sort": "date"},
                    headers=headers,
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()

                for article in data.get("items", []):
                    # HTML 태그 제거
                    title = article["title"].replace("<b>", "").replace("</b>", "")
                    items.append(TrendingItem(
                        title=title,
                        source="naver",
                        category="",
                        score_raw=30,  # 뉴스는 기본 점수
                        url=article.get("link", ""),
                        region="KR",
                        metadata={"type": "news", "query": query},
                    ))

            except Exception as e:
                log.error(f"네이버 뉴스 '{query}' 실패: {e}")

        log.info(f"네이버 뉴스: {len(items)}개 수집")
        return items

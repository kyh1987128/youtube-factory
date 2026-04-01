"""YouTube 인기 동영상 수집기 - YouTube Data API v3."""
import logging
import os

from youtube_factory.collectors import BaseCollector
from youtube_factory.models import TrendingItem

log = logging.getLogger(__name__)

# 키워드 → 카테고리 매핑
CATEGORY_KEYWORDS = {
    "tech": ["AI", "인공지능", "GPT", "반도체", "chip", "software", "코딩", "개발", "robot", "로봇", "테크"],
    "finance": ["주식", "코인", "비트코인", "투자", "경제", "부동산", "stock", "crypto", "금리"],
    "health": ["건강", "운동", "다이어트", "식단", "health", "fitness", "의학"],
    "education": ["공부", "학습", "강의", "대학", "취업", "자격증", "education"],
    "entertainment": ["게임", "영화", "드라마", "음악", "예능", "game", "movie", "music"],
    "lifestyle": ["여행", "맛집", "요리", "일상", "브이로그", "travel", "food", "vlog"],
}


def _guess_category(title: str, tags: list[str]) -> str:
    """제목과 태그에서 카테고리 추정."""
    text = (title + " " + " ".join(tags)).lower()
    best, best_count = "general", 0
    for cat, keywords in CATEGORY_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw.lower() in text)
        if count > best_count:
            best, best_count = cat, count
    return best


class YouTubeTrendingCollector(BaseCollector):
    name = "youtube_trending"

    def collect(self) -> list[TrendingItem]:
        api_key = os.environ.get("YOUTUBE_API_KEY")
        if not api_key:
            log.warning("YOUTUBE_API_KEY 미설정 - YouTube 수집 건너뜀")
            return []

        try:
            from googleapiclient.discovery import build
            youtube = build("youtube", "v3", developerKey=api_key)
        except Exception as e:
            log.error(f"YouTube API 초기화 실패: {e}")
            return []

        regions = self.config.get("regions", ["KR", "US"])
        max_results = self.config.get("max_results", 30)
        items = []

        for region in regions:
            try:
                resp = youtube.videos().list(
                    part="snippet,statistics",
                    chart="mostPopular",
                    regionCode=region,
                    maxResults=max_results,
                ).execute()

                for video in resp.get("items", []):
                    snippet = video["snippet"]
                    stats = video.get("statistics", {})
                    views = int(stats.get("viewCount", 0))
                    likes = int(stats.get("likeCount", 0))
                    comments = int(stats.get("commentCount", 0))
                    tags = snippet.get("tags", [])

                    # 반응도 점수 계산
                    score = views * 0.4 + likes * 100 * 0.4 + comments * 500 * 0.2

                    items.append(TrendingItem(
                        title=snippet["title"],
                        source="youtube",
                        category=_guess_category(snippet["title"], tags),
                        score_raw=score,
                        url=f"https://youtu.be/{video['id']}",
                        view_count=views,
                        like_count=likes,
                        comment_count=comments,
                        region=region,
                        metadata={"channel": snippet.get("channelTitle", ""), "tags": tags},
                    ))

                log.info(f"YouTube {region}: {len(resp.get('items', []))}개 수집")

            except Exception as e:
                log.error(f"YouTube {region} 수집 실패: {e}")

        return items

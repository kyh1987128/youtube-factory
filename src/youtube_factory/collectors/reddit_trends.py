"""Reddit 트렌딩 수집기 - PRAW 사용."""
import logging
import os
import time

from youtube_factory.collectors import BaseCollector
from youtube_factory.models import TrendingItem

log = logging.getLogger(__name__)

# 카테고리별 서브레딧 매핑
CATEGORY_SUBREDDITS = {
    "tech": ["technology", "programming", "artificial", "MachineLearning"],
    "finance": ["investing", "CryptoCurrency", "personalfinance", "stocks"],
    "health": ["fitness", "nutrition", "HealthyFood"],
    "entertainment": ["gaming", "movies", "music", "television"],
    "education": ["learnprogramming", "datascience", "AskScience"],
    "lifestyle": ["travel", "food", "DIY"],
}


class RedditTrendsCollector(BaseCollector):
    name = "reddit_trends"

    def collect(self) -> list[TrendingItem]:
        client_id = os.environ.get("REDDIT_CLIENT_ID")
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        user_agent = os.environ.get("REDDIT_USER_AGENT", "youtube-factory/0.1")

        if not client_id or not client_secret:
            log.warning("REDDIT_CLIENT_ID/SECRET 미설정 - Reddit 수집 건너뜀")
            return []

        try:
            import praw
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )
        except Exception as e:
            log.error(f"Reddit API 초기화 실패: {e}")
            return []

        items = []

        # 1. r/all 인기 게시물
        items.extend(self._collect_hot(reddit))

        # 2. 카테고리별 서브레딧
        subreddits = self.config.get("subreddits", [])
        if not subreddits:
            items.extend(self._collect_by_category(reddit))
        else:
            for sub_name in subreddits:
                items.extend(self._collect_subreddit(reddit, sub_name, ""))

        return items

    def _collect_hot(self, reddit) -> list[TrendingItem]:
        """r/all 핫 게시물 수집."""
        items = []
        try:
            for post in reddit.subreddit("all").hot(limit=30):
                items.append(self._post_to_item(post, "general"))

            # 급상승 게시물
            for post in reddit.subreddit("all").rising(limit=20):
                item = self._post_to_item(post, "general")
                item.trend_velocity = 2.0  # 급상승 보너스
                items.append(item)

            log.info(f"Reddit r/all: {len(items)}개 수집")
        except Exception as e:
            log.error(f"Reddit r/all 수집 실패: {e}")

        return items

    def _collect_by_category(self, reddit) -> list[TrendingItem]:
        """카테고리별 서브레딧에서 수집."""
        items = []
        for category, subs in CATEGORY_SUBREDDITS.items():
            for sub_name in subs:
                items.extend(self._collect_subreddit(reddit, sub_name, category))
        return items

    def _collect_subreddit(self, reddit, sub_name: str, category: str) -> list[TrendingItem]:
        """개별 서브레딧에서 인기 게시물 수집."""
        items = []
        try:
            for post in reddit.subreddit(sub_name).hot(limit=10):
                items.append(self._post_to_item(post, category))
            log.info(f"Reddit r/{sub_name}: {len(items)}개 수집")
        except Exception as e:
            log.debug(f"Reddit r/{sub_name} 실패: {e}")
        return items

    def _post_to_item(self, post, category: str) -> TrendingItem:
        """Reddit 포스트 → TrendingItem 변환."""
        now = time.time()
        hours_age = max(1, (now - post.created_utc) / 3600)
        velocity = post.score / hours_age

        # 반응도 점수: 업보트 * 비율 + 댓글
        score = post.score * post.upvote_ratio * 0.6 + post.num_comments * 10 * 0.4

        return TrendingItem(
            title=post.title,
            source="reddit",
            category=category,
            score_raw=score,
            url=f"https://reddit.com{post.permalink}",
            view_count=0,
            like_count=post.score,
            comment_count=post.num_comments,
            trend_velocity=velocity,
            region="US",
            metadata={
                "subreddit": post.subreddit.display_name,
                "upvote_ratio": post.upvote_ratio,
            },
        )

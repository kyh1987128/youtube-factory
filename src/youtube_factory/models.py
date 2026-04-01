"""파이프라인 전체에서 공유되는 데이터 모델."""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TrendingItem:
    """수집된 트렌딩 항목."""
    title: str
    source: str          # "youtube", "google_trends", "naver", "reddit"
    category: str = ""   # "tech", "finance", "health" 등
    score_raw: float = 0.0
    url: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    trend_velocity: float = 0.0
    region: str = ""     # "KR", "US" 등
    metadata: dict = field(default_factory=dict)


@dataclass
class ScoredTopic:
    """점수가 매겨진 주제 후보."""
    title: str
    category: str
    final_score: float
    sources: list[str] = field(default_factory=list)
    source_count: int = 0
    items: list[TrendingItem] = field(default_factory=list)


@dataclass
class Scene:
    """스크립트의 개별 장면."""
    index: int
    narration: str
    visual_prompt: str
    duration: float = 0.0
    audio_path: Path | None = None
    image_path: Path | None = None


@dataclass
class PipelineContext:
    """스테이지 간 전달되는 파이프라인 컨텍스트."""
    work_dir: Path = field(default_factory=lambda: Path("./output"))

    # Stage 1: topic
    topic: str = ""
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)

    # Stage 2: script
    scenes: list[Scene] = field(default_factory=list)

    # Stage 5: assembly
    video_path: Path | None = None

    # Stage 6: thumbnail
    thumbnail_path: Path | None = None

    # Stage 7: upload
    video_id: str = ""
    video_url: str = ""

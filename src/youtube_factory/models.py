"""파이프라인 전체에서 공유되는 데이터 모델."""
from dataclasses import dataclass, field
from pathlib import Path


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

    # 모드 정보
    mode: str = "trending"
    source_urls: list[str] = field(default_factory=list)
    target_language: str = "ko"
    target_category: str = ""
    platform: str = ""          # platform 모드용 (reddit/tiktok/news)
    direction: str = ""         # short 모드용 (long2short/short2long)

    # Stage: topic
    topic: str = ""
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)

    # Stage: transcript (대본 추출)
    source_transcripts: list[str] = field(default_factory=list)

    # Stage: analyze (분석 결과)
    source_analysis: str = ""

    # Stage: adapt (변형된 스크립트)
    adapted_script: str = ""

    # Stage: script (장면 분할)
    scenes: list[Scene] = field(default_factory=list)

    # Stage: assembly
    video_path: Path | None = None

    # Stage: thumbnail
    thumbnail_path: Path | None = None

    # Stage: upload
    video_id: str = ""
    video_url: str = ""

"""스테이지 추상 베이스 클래스."""
from abc import ABC, abstractmethod

from youtube_factory.models import PipelineContext


class Stage(ABC):
    """모든 파이프라인 스테이지의 베이스 클래스."""

    def __init__(self, config: dict):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def run(self, ctx: PipelineContext) -> PipelineContext:
        ...

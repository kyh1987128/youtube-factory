"""트렌딩 데이터 수집기 모듈."""
from abc import ABC, abstractmethod

from youtube_factory.models import TrendingItem


class BaseCollector(ABC):
    """데이터 수집기 베이스 클래스."""

    def __init__(self, config: dict):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def collect(self) -> list[TrendingItem]:
        """트렌딩 데이터 수집. 실패 시 빈 리스트 반환."""
        ...

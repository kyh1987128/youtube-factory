"""주제 리서치 스테이지 - Claude Code가 웹 검색으로 트렌딩 조사 + 주제 선정."""
import json
import logging

from youtube_factory.claude_cli import ask_claude
from youtube_factory.models import PipelineContext

log = logging.getLogger(__name__)


class TopicStage:
    name = "topic"

    def __init__(self, config: dict):
        self.config = config

    def run(self, ctx: PipelineContext) -> PipelineContext:
        category = self.config.get("category", "tech")
        language = self.config.get("language", "ko")
        preferred = self.config.get("preferred_categories", ["tech", "finance", "education"])

        prompt = (
            f"유튜브 영상 주제를 선정하기 위해 현재 트렌딩을 조사해줘.\n\n"
            f"## 조사 방법\n"
            f"1. 구글에서 한국/해외 실시간 트렌딩 키워드 검색\n"
            f"2. 유튜브에서 현재 인기 급상승 영상 확인\n"
            f"3. 네이버에서 실시간 검색어/뉴스 트렌드 확인\n"
            f"4. 레딧에서 해외 핫 토픽 확인\n\n"
            f"## 조건\n"
            f"- 선호 카테고리: {', '.join(preferred)}\n"
            f"- 영상 언어: {language}\n"
            f"- 대상: 한국 유튜브 시청자\n"
            f"- 여러 플랫폼에서 동시에 화제인 주제 우선\n"
            f"- 조회수/반응도가 높을 만한 주제\n"
            f"- 영상으로 만들었을 때 클릭률이 높을 주제\n\n"
            f"## 요청\n"
            f"웹 검색으로 실제 트렌딩 데이터를 조사한 뒤,\n"
            f"가장 좋은 주제 1개를 골라서 유튜브 영상용으로 다듬어줘.\n\n"
            f"반드시 아래 JSON 형식으로만 응답해 (다른 텍스트 없이):\n"
            f'{{"topic": "선정 주제 설명", "title": "유튜브 영상 제목 (클릭 유도형)", '
            f'"description": "영상 설명 (2-3문장)", "tags": ["태그1", "태그2", "태그3", "태그4", "태그5"], '
            f'"reasoning": "이 주제를 선택한 이유 (어디서 트렌딩인지 포함)"}}'
        )

        log.info("Claude Code로 트렌딩 조사 중 (웹 검색)...")
        text = ask_claude(prompt, timeout=180)

        # JSON 파싱
        if "```" in text:
            text = text.split("```json")[-1].split("```")[0] if "```json" in text else text.split("```")[1].split("```")[0]
        data = json.loads(text.strip())

        ctx.topic = data["topic"]
        ctx.title = data["title"]
        ctx.description = data["description"]
        ctx.tags = data["tags"]

        log.info(f"주제 선정: {ctx.title}")
        log.info(f"선정 이유: {data.get('reasoning', '')}")
        return ctx

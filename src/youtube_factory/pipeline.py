"""파이프라인 오케스트레이터 - 모드별 스테이지 체인 + 승인 게이트."""
import logging
import time
from pathlib import Path

from youtube_factory.models import PipelineContext
from youtube_factory.stages.adapt import AdaptStage
from youtube_factory.stages.analyze import AnalyzeStage
from youtube_factory.stages.assembly import AssemblyStage
from youtube_factory.stages.base import Stage
from youtube_factory.stages.export import ExportStage
from youtube_factory.stages.script import ScriptStage
from youtube_factory.stages.thumbnail import ThumbnailStage
from youtube_factory.stages.topic import TopicStage
from youtube_factory.stages.transcript import TranscriptStage
from youtube_factory.stages.upload import UploadStage
from youtube_factory.stages.visuals import VisualsStage
from youtube_factory.stages.voice import VoiceStage

log = logging.getLogger(__name__)

STAGE_REGISTRY: dict[str, type[Stage]] = {
    "topic": TopicStage,
    "transcript": TranscriptStage,
    "analyze": AnalyzeStage,
    "adapt": AdaptStage,
    "script": ScriptStage,
    "voice": VoiceStage,
    "visuals": VisualsStage,
    "assembly": AssemblyStage,
    "thumbnail": ThumbnailStage,
    "export": ExportStage,
    "upload": UploadStage,
}

# 모드별 스테이지 체인
MODE_STAGES = {
    "trending": [
        "topic", "script", "voice", "visuals", "assembly", "thumbnail", "export",
    ],
    "cross-lang": [
        "topic", "transcript", "analyze", "adapt", "script",
        "voice", "visuals", "assembly", "thumbnail", "export",
    ],
    "cross-lang-reverse": [
        "topic", "transcript", "analyze", "adapt", "script",
        "voice", "visuals", "assembly", "thumbnail", "export",
    ],
    "platform": [
        "topic", "analyze", "adapt", "script",
        "voice", "visuals", "assembly", "thumbnail", "export",
    ],
    "short-long2short": [
        "transcript", "analyze", "script",
        "voice", "visuals", "assembly", "thumbnail", "export",
    ],
    "short-short2long": [
        "topic", "transcript", "analyze", "adapt", "script",
        "voice", "visuals", "assembly", "thumbnail", "export",
    ],
    "format-cross": [
        "transcript", "analyze", "topic", "adapt", "script",
        "voice", "visuals", "assembly", "thumbnail", "export",
    ],
}

# 모드별 승인 게이트 위치
MODE_APPROVAL_GATES = {
    "trending": {"topic": "approve_topic", "export": "approve_final"},
    "cross-lang": {"adapt": "approve_adapt", "export": "approve_final"},
    "cross-lang-reverse": {"adapt": "approve_adapt", "export": "approve_final"},
    "platform": {"adapt": "approve_adapt", "export": "approve_final"},
    "short-long2short": {"script": "approve_topic", "export": "approve_final"},
    "short-short2long": {"adapt": "approve_adapt", "export": "approve_final"},
    "format-cross": {"adapt": "approve_adapt", "export": "approve_final"},
}


def run_pipeline(
    config: dict,
    topic_override: str | None = None,
    auto_approve: bool = False,
    mode: str = "trending",
    source_urls: list[str] | None = None,
    target_language: str = "ko",
    target_category: str = "",
    platform: str = "",
    direction: str = "",
) -> PipelineContext:
    """설정에 따라 파이프라인 실행."""
    work_dir = Path(config["pipeline"]["output_dir"]) / f"run_{int(time.time())}"
    work_dir.mkdir(parents=True, exist_ok=True)

    # short 모드는 direction에 따라 세부 모드 결정
    if mode == "short":
        mode = f"short-{direction or 'long2short'}"

    ctx = PipelineContext(
        work_dir=work_dir,
        mode=mode,
        source_urls=source_urls or [],
        target_language=target_language,
        target_category=target_category,
        platform=platform,
        direction=direction,
    )

    # 주제 직접 지정
    if topic_override:
        ctx.topic = topic_override
        ctx.title = topic_override

    # 모드별 스테이지 체인
    stage_names = config["pipeline"].get("stages") or MODE_STAGES.get(mode)
    if not stage_names:
        raise ValueError(f"알 수 없는 모드: {mode}")

    # topic_override가 있으면 topic 스테이지 스킵
    if topic_override and "topic" in stage_names:
        stage_names = [s for s in stage_names if s != "topic"]

    # 승인 게이트 설정
    gates = MODE_APPROVAL_GATES.get(mode, {})

    log.info(f"모드: {mode} | 스테이지: {' → '.join(stage_names)}")

    total = len(stage_names)
    for i, name in enumerate(stage_names, 1):
        if name not in STAGE_REGISTRY:
            raise ValueError(f"알 수 없는 스테이지: {name}")

        stage_config = config.get(name, {})
        stage = STAGE_REGISTRY[name](stage_config)

        log.info(f"[{i}/{total}] '{name}' 스테이지 시작")
        start = time.time()
        ctx = stage.run(ctx)
        elapsed = time.time() - start
        log.info(f"[{i}/{total}] '{name}' 스테이지 완료 ({elapsed:.1f}초)")

        # 승인 게이트 체크
        if not auto_approve and name in gates:
            from youtube_factory.approval import approve_topic, approve_adapt, approve_final

            gate = gates[name]
            if gate == "approve_topic":
                ctx = approve_topic(ctx, config)
            elif gate == "approve_adapt":
                ctx = approve_adapt(ctx)
            elif gate == "approve_final":
                ctx = approve_final(ctx)

    return ctx

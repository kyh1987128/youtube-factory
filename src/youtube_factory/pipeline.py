"""파이프라인 오케스트레이터 - 스테이지를 순차 실행 + 승인 게이트."""
import logging
import time
from pathlib import Path

from youtube_factory.models import PipelineContext
from youtube_factory.stages.assembly import AssemblyStage
from youtube_factory.stages.base import Stage
from youtube_factory.stages.export import ExportStage
from youtube_factory.stages.script import ScriptStage
from youtube_factory.stages.thumbnail import ThumbnailStage
from youtube_factory.stages.topic import TopicStage
from youtube_factory.stages.upload import UploadStage
from youtube_factory.stages.visuals import VisualsStage
from youtube_factory.stages.voice import VoiceStage

log = logging.getLogger(__name__)

STAGE_REGISTRY: dict[str, type[Stage]] = {
    "topic": TopicStage,
    "script": ScriptStage,
    "voice": VoiceStage,
    "visuals": VisualsStage,
    "assembly": AssemblyStage,
    "thumbnail": ThumbnailStage,
    "export": ExportStage,
    "upload": UploadStage,
}

# 승인 게이트: 이 스테이지 완료 후 사람 승인을 받음
APPROVAL_GATES = {
    "topic": "approve_topic",   # 주제 선정 후
    "export": "approve_final",  # 최종 소재 내보내기 후 (영상+썸네일+소재 다 나온 뒤)
}


def run_pipeline(
    config: dict,
    topic_override: str | None = None,
    auto_approve: bool = False,
) -> PipelineContext:
    """설정에 따라 파이프라인 실행.

    Args:
        config: YAML 설정
        topic_override: 주제 직접 지정 시
        auto_approve: True면 승인 게이트 건너뜀 (CI/스케줄러용)
    """
    stage_names = config["pipeline"]["stages"]
    work_dir = Path(config["pipeline"]["output_dir"]) / f"run_{int(time.time())}"
    work_dir.mkdir(parents=True, exist_ok=True)

    ctx = PipelineContext(work_dir=work_dir)

    # 주제가 직접 지정된 경우
    if topic_override:
        ctx.topic = topic_override
        ctx.title = topic_override
        stage_names = [s for s in stage_names if s != "topic"]
        log.info(f"주제 직접 지정: {topic_override}")

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
        if not auto_approve and name in APPROVAL_GATES:
            from youtube_factory.approval import approve_topic, approve_final

            gate = APPROVAL_GATES[name]
            if gate == "approve_topic":
                ctx = approve_topic(ctx, config)
            elif gate == "approve_final":
                ctx = approve_final(ctx)

    return ctx

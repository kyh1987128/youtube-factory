"""음성 생성 스테이지 - edge-tts로 나레이션 TTS."""
import asyncio
import logging
import struct
import subprocess

import edge_tts

from youtube_factory.models import PipelineContext
from youtube_factory.stages.base import Stage

log = logging.getLogger(__name__)


def _get_mp3_duration(path: str) -> float:
    """ffprobe로 MP3 파일의 정확한 길이(초) 측정."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                path,
            ],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        # ffprobe 없으면 파일 크기 기반 추정 (128kbps 가정)
        import os
        size = os.path.getsize(path)
        return size / (128 * 1000 / 8)


class VoiceStage(Stage):
    name = "voice"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        voice_name = self.config.get("voice_name", "ko-KR-SunHiNeural")
        rate = self.config.get("rate", "+0%")

        async def generate_all():
            for scene in ctx.scenes:
                out_path = ctx.work_dir / f"voice_{scene.index:03d}.mp3"
                log.info(f"장면 {scene.index} 음성 생성 중...")
                comm = edge_tts.Communicate(scene.narration, voice_name, rate=rate)
                await comm.save(str(out_path))
                scene.audio_path = out_path

        asyncio.run(generate_all())

        # 각 장면의 음성 길이 측정 (Remotion에 전달하기 위해 필수)
        for scene in ctx.scenes:
            if scene.audio_path:
                scene.duration = _get_mp3_duration(str(scene.audio_path))
                log.info(f"장면 {scene.index}: {scene.duration:.1f}초")

        total = sum(s.duration for s in ctx.scenes)
        log.info(f"음성 생성 완료: {len(ctx.scenes)}개 파일, 총 {total:.1f}초")
        return ctx

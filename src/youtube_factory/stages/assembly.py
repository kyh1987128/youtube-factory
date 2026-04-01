"""영상 조립 스테이지 - Remotion으로 최종 영상 렌더링.

Python에서 장면 데이터를 JSON으로 생성 → Remotion CLI가 렌더링.
"""
import json
import logging
import subprocess
from pathlib import Path

from youtube_factory.models import PipelineContext
from youtube_factory.stages.base import Stage

log = logging.getLogger(__name__)

# Remotion 프로젝트 경로 (youtube-factory/remotion/)
REMOTION_DIR = Path(__file__).resolve().parents[3] / "remotion"


class AssemblyStage(Stage):
    name = "assembly"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        fps = self.config.get("fps", 30)
        width = self.config.get("width", 1920)
        height = self.config.get("height", 1080)

        # 1. Remotion용 JSON 데이터 생성
        props = self._build_props(ctx, fps, width, height)
        props_path = ctx.work_dir / "remotion_props.json"
        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False, indent=2)

        log.info(f"Remotion 프로퍼티 생성: {props_path}")

        # 2. Remotion CLI로 렌더링
        out_path = ctx.work_dir / "final_video.mp4"
        self._render(props_path, out_path)

        ctx.video_path = out_path
        total_duration = sum(s.duration for s in ctx.scenes)
        log.info(f"영상 렌더링 완료: {total_duration:.1f}초, {out_path}")
        return ctx

    def _build_props(self, ctx: PipelineContext, fps: int, width: int, height: int) -> dict:
        """Remotion에 전달할 props JSON 생성."""
        # 이미지/오디오 경로를 절대 경로로 변환 (file:// URI)
        scenes = []
        for scene in ctx.scenes:
            audio_path = str(scene.audio_path.resolve()) if scene.audio_path else ""
            image_path = str(scene.image_path.resolve()) if scene.image_path else ""

            scenes.append({
                "index": scene.index,
                "narration": scene.narration,
                "visualPrompt": scene.visual_prompt,
                "duration": scene.duration,
                "audioFile": audio_path,
                "imageFile": image_path,
            })

        return {
            "data": {
                "title": ctx.title,
                "description": ctx.description,
                "tags": ctx.tags,
                "scenes": scenes,
                "config": {
                    "fps": fps,
                    "width": width,
                    "height": height,
                    "subtitle": {
                        "enabled": self.config.get("subtitle_enabled", True),
                        "fontSize": self.config.get("subtitle_font_size", 48),
                        "fontFamily": self.config.get("subtitle_font", "Malgun Gothic, sans-serif"),
                        "color": "#FFFFFF",
                        "backgroundColor": "rgba(0,0,0,0.6)",
                        "position": self.config.get("subtitle_position", "bottom"),
                    },
                    "transition": {
                        "type": self.config.get("transition_type", "fade"),
                        "durationFrames": int(self.config.get("transition_duration", 0.5) * fps),
                    },
                    "kenBurns": {
                        "enabled": self.config.get("ken_burns", True),
                        "zoomRange": self.config.get("ken_burns_range", [1.0, 1.12]),
                    },
                    "bgm": {
                        "enabled": bool(self.config.get("bgm_file")),
                        "file": self.config.get("bgm_file", ""),
                        "volume": self.config.get("bgm_volume", 0.3),
                        "duckingVolume": self.config.get("bgm_ducking_volume", 0.1),
                    },
                },
            }
        }

    def _render(self, props_path: Path, out_path: Path):
        """Remotion CLI를 subprocess로 호출하여 렌더링."""
        entry_point = REMOTION_DIR / "src" / "index.ts"
        concurrency = self.config.get("render_concurrency", 2)

        cmd = [
            "npx", "remotion", "render",
            str(entry_point),
            "YouTubeVideo",
            "--output", str(out_path),
            "--props", str(props_path),
            "--concurrency", str(concurrency),
        ]

        # 선택적 옵션
        codec = self.config.get("codec", "h264")
        cmd.extend(["--codec", codec])

        log.info(f"Remotion 렌더링 시작...")
        log.info(f"명령어: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=str(REMOTION_DIR),
            capture_output=True,
            text=True,
            timeout=self.config.get("render_timeout", 600),
        )

        if result.returncode != 0:
            log.error(f"Remotion 렌더링 실패:\n{result.stderr}")
            raise RuntimeError(f"Remotion render failed: {result.stderr[-500:]}")

        log.info("Remotion 렌더링 성공")
        if result.stdout:
            # 마지막 몇 줄만 로깅
            for line in result.stdout.strip().split("\n")[-5:]:
                log.info(f"  {line}")

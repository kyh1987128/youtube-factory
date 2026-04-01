"""소재 내보내기 스테이지 - CapCut 등 외부 편집기용 소재 정리.

output/run_XXXX/
├── capcut_assets/
│   ├── 00_인트로/
│   │   ├── voice.mp3
│   │   ├── image.png
│   │   └── narration.txt
│   ├── 01_장면제목/
│   │   ├── voice.mp3
│   │   ├── image.png
│   │   └── narration.txt
│   ├── ...
│   ├── thumbnail.png
│   ├── script.txt         ← 전체 스크립트
│   └── timeline.txt       ← 타임라인 가이드
"""
import json
import logging
import shutil

from youtube_factory.models import PipelineContext
from youtube_factory.stages.base import Stage

log = logging.getLogger(__name__)


class ExportStage(Stage):
    name = "export"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        export_dir = ctx.work_dir / "capcut_assets"
        export_dir.mkdir(exist_ok=True)

        # 1. 장면별 폴더 생성
        for scene in ctx.scenes:
            # 폴더명: 번호_나레이션앞부분 (CapCut에서 정렬 쉽도록)
            label = scene.narration[:20].replace(" ", "_").replace("/", "_")
            scene_dir = export_dir / f"{scene.index:02d}_{label}"
            scene_dir.mkdir(exist_ok=True)

            # 음성 복사
            if scene.audio_path and scene.audio_path.exists():
                shutil.copy2(scene.audio_path, scene_dir / "voice.mp3")

            # 이미지 복사
            if scene.image_path and scene.image_path.exists():
                suffix = scene.image_path.suffix
                shutil.copy2(scene.image_path, scene_dir / f"image{suffix}")

            # 나레이션 텍스트
            with open(scene_dir / "narration.txt", "w", encoding="utf-8") as f:
                f.write(scene.narration)

        # 2. 썸네일 복사
        if ctx.thumbnail_path and ctx.thumbnail_path.exists():
            shutil.copy2(ctx.thumbnail_path, export_dir / "thumbnail.png")

        # 3. 전체 스크립트
        with open(export_dir / "script.txt", "w", encoding="utf-8") as f:
            f.write(f"제목: {ctx.title}\n")
            f.write(f"설명: {ctx.description}\n")
            f.write(f"태그: {', '.join(ctx.tags)}\n")
            f.write(f"{'='*60}\n\n")
            for scene in ctx.scenes:
                f.write(f"[장면 {scene.index + 1}] ({scene.duration:.1f}초)\n")
                f.write(f"{scene.narration}\n")
                f.write(f"→ 비주얼: {scene.visual_prompt}\n\n")

        # 4. 타임라인 가이드 (CapCut에서 참고용)
        self._write_timeline(ctx, export_dir)

        # 5. 메타데이터 JSON (프로그래밍 연동용)
        self._write_metadata(ctx, export_dir)

        log.info(f"CapCut 소재 내보내기 완료: {export_dir}")
        log.info(f"  → {len(ctx.scenes)}개 장면 폴더")
        log.info(f"  → CapCut에서 폴더 순서대로 타임라인에 배치하세요")
        return ctx

    def _write_timeline(self, ctx: PipelineContext, export_dir):
        """타임라인 가이드 생성."""
        with open(export_dir / "timeline.txt", "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"  {ctx.title} - 타임라인 가이드\n")
            f.write("=" * 60 + "\n\n")
            f.write("CapCut 편집 순서:\n")
            f.write("1. capcut_assets 폴더의 장면 폴더를 번호순으로 열기\n")
            f.write("2. 각 폴더의 image → 비디오 트랙, voice.mp3 → 오디오 트랙\n")
            f.write("3. narration.txt 참고하여 자막 추가\n")
            f.write("4. 장면 전환 효과 추가\n")
            f.write("5. BGM 추가\n\n")

            f.write("-" * 60 + "\n")
            f.write(f"{'장면':>6} | {'시작':>8} | {'길이':>6} | 내용\n")
            f.write("-" * 60 + "\n")

            current_time = 0.0
            total_duration = 0.0
            for scene in ctx.scenes:
                dur = scene.duration
                minutes = int(current_time // 60)
                seconds = current_time % 60
                f.write(
                    f"{scene.index + 1:>6} | "
                    f"{minutes:02d}:{seconds:05.2f} | "
                    f"{dur:5.1f}s | "
                    f"{scene.narration[:40]}...\n"
                )
                current_time += dur
                total_duration += dur

            f.write("-" * 60 + "\n")
            f.write(f"총 길이: {total_duration:.1f}초 ({total_duration/60:.1f}분)\n")

    def _write_metadata(self, ctx: PipelineContext, export_dir):
        """JSON 메타데이터 (자동화 연동용)."""
        meta = {
            "title": ctx.title,
            "description": ctx.description,
            "tags": ctx.tags,
            "total_scenes": len(ctx.scenes),
            "total_duration": sum(s.duration for s in ctx.scenes),
            "scenes": [
                {
                    "index": s.index,
                    "narration": s.narration,
                    "visual_prompt": s.visual_prompt,
                    "duration": s.duration,
                    "audio_file": f"{s.index:02d}_*/voice.mp3",
                    "image_file": f"{s.index:02d}_*/image.png",
                }
                for s in ctx.scenes
            ],
        }
        with open(export_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

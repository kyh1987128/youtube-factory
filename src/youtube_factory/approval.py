"""승인 게이트 - 파이프라인 중간에 사람 확인/수정 후 진행."""
import json
import logging
import os
import sys

from youtube_factory.models import PipelineContext

log = logging.getLogger(__name__)

# ANSI 색상 (Windows Terminal 지원)
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def approve_topic(ctx: PipelineContext, config: dict) -> PipelineContext:
    """주제 선정 후 승인 게이트.

    사용자가 승인(y), 재생성(r), 직접 수정(e), 중단(q) 선택 가능.
    """
    while True:
        print(f"\n{'='*60}")
        print(f"{BOLD}{CYAN}  📋 주제 승인 요청{RESET}")
        print(f"{'='*60}")
        print(f"\n  {BOLD}제목:{RESET}  {ctx.title}")
        print(f"  {BOLD}주제:{RESET}  {ctx.topic}")
        print(f"  {BOLD}설명:{RESET}  {ctx.description}")
        print(f"  {BOLD}태그:{RESET}  {', '.join(ctx.tags)}")
        print(f"\n{'─'*60}")
        print(f"  {GREEN}[y] 승인{RESET} - 이 주제로 진행")
        print(f"  {YELLOW}[r] 재생성{RESET} - 다른 주제 다시 뽑기")
        print(f"  {CYAN}[e] 수정{RESET} - 제목/설명을 직접 수정")
        print(f"  {RED}[q] 중단{RESET} - 파이프라인 중단")
        print(f"{'─'*60}")

        choice = input(f"\n  선택: ").strip().lower()

        if choice in ("y", "yes", ""):
            log.info("주제 승인됨")
            print(f"\n  {GREEN}✓ 승인 완료 - 다음 단계로 진행합니다{RESET}\n")
            return ctx

        elif choice in ("r", "retry"):
            print(f"\n  {YELLOW}↻ 주제를 다시 생성합니다...{RESET}\n")
            # topic 스테이지를 다시 실행
            from youtube_factory.stages.topic import TopicStage
            stage = TopicStage(config.get("topic", {}))
            ctx = stage.run(ctx)
            continue

        elif choice in ("e", "edit"):
            ctx = _edit_topic(ctx)
            continue  # 수정 후 다시 보여줌

        elif choice in ("q", "quit"):
            print(f"\n  {RED}✗ 파이프라인을 중단합니다{RESET}\n")
            sys.exit(0)

        else:
            print(f"  {DIM}y/r/e/q 중 선택해주세요{RESET}")


def _edit_topic(ctx: PipelineContext) -> PipelineContext:
    """주제 정보를 대화형으로 수정."""
    print(f"\n  {CYAN}수정할 항목만 입력하세요 (빈칸 = 유지){RESET}\n")

    new_title = input(f"  제목 [{ctx.title}]: ").strip()
    if new_title:
        ctx.title = new_title

    new_topic = input(f"  주제 [{ctx.topic}]: ").strip()
    if new_topic:
        ctx.topic = new_topic

    new_desc = input(f"  설명 [{ctx.description}]: ").strip()
    if new_desc:
        ctx.description = new_desc

    new_tags = input(f"  태그 [{', '.join(ctx.tags)}] (쉼표 구분): ").strip()
    if new_tags:
        ctx.tags = [t.strip() for t in new_tags.split(",") if t.strip()]

    print(f"\n  {GREEN}✓ 수정 완료{RESET}")
    return ctx


def approve_final(ctx: PipelineContext) -> PipelineContext:
    """최종 영상 렌더링 후 승인 게이트.

    영상 파일과 소재를 확인 후 업로드 진행 여부 결정.
    """
    total_duration = sum(s.duration for s in ctx.scenes)
    minutes = int(total_duration // 60)
    seconds = int(total_duration % 60)

    print(f"\n{'='*60}")
    print(f"{BOLD}{CYAN}  🎬 최종 영상 승인 요청{RESET}")
    print(f"{'='*60}")
    print(f"\n  {BOLD}제목:{RESET}     {ctx.title}")
    print(f"  {BOLD}길이:{RESET}     {minutes}분 {seconds}초 ({len(ctx.scenes)}개 장면)")

    if ctx.video_path and ctx.video_path.exists():
        size_mb = ctx.video_path.stat().st_size / (1024 * 1024)
        print(f"  {BOLD}영상:{RESET}     {ctx.video_path} ({size_mb:.1f}MB)")

    if ctx.thumbnail_path and ctx.thumbnail_path.exists():
        print(f"  {BOLD}썸네일:{RESET}   {ctx.thumbnail_path}")

    export_dir = ctx.work_dir / "capcut_assets"
    if export_dir.exists():
        print(f"  {BOLD}소재폴더:{RESET} {export_dir}")

    print(f"\n  {BOLD}장면 목록:{RESET}")
    for scene in ctx.scenes:
        print(f"    {DIM}[{scene.index+1:2d}]{RESET} {scene.duration:.1f}s │ {scene.narration[:45]}...")

    print(f"\n{'─'*60}")
    print(f"  {GREEN}[y] 승인{RESET} - 업로드 단계로 진행 (또는 완료)")
    print(f"  {CYAN}[o] 열기{RESET} - 영상 파일 열어서 확인")
    print(f"  {CYAN}[f] 폴더{RESET} - 소재 폴더 열기 (CapCut 편집용)")
    print(f"  {RED}[q] 중단{RESET} - 여기서 중단 (소재는 보존)")
    print(f"{'─'*60}")

    while True:
        choice = input(f"\n  선택: ").strip().lower()

        if choice in ("y", "yes", ""):
            log.info("최종 영상 승인됨")
            print(f"\n  {GREEN}✓ 승인 완료{RESET}\n")
            return ctx

        elif choice in ("o", "open"):
            _open_file(ctx.video_path)

        elif choice in ("f", "folder"):
            _open_file(export_dir if export_dir.exists() else ctx.work_dir)

        elif choice in ("q", "quit"):
            print(f"\n  파이프라인을 중단합니다.")
            print(f"  소재 위치: {ctx.work_dir}")
            print(f"  {DIM}CapCut에서 소재를 열어 직접 편집할 수 있습니다{RESET}\n")
            sys.exit(0)

        else:
            print(f"  {DIM}y/o/f/q 중 선택해주세요{RESET}")


def _open_file(path):
    """파일 또는 폴더를 시스템 기본 프로그램으로 열기."""
    if path and path.exists():
        os.startfile(str(path))
        print(f"  {DIM}열기: {path}{RESET}")
    else:
        print(f"  {DIM}파일을 찾을 수 없습니다: {path}{RESET}")

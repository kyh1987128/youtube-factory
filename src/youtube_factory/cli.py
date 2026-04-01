"""CLI 진입점."""
import argparse
import logging

from youtube_factory.config import load_config
from youtube_factory.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Factory - AI 콘텐츠 자동 생산"
    )
    parser.add_argument("-c", "--config", default="config.yaml", help="설정 파일 경로")
    parser.add_argument("--stages", nargs="+", help="실행할 스테이지 (예: topic script)")
    parser.add_argument("--topic", help="주제 직접 지정 (topic 스테이지 스킵)")
    parser.add_argument("--auto-approve", action="store_true",
                        help="승인 게이트 건너뜀 (스케줄러/CI용)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(args.config)

    if args.stages:
        config["pipeline"]["stages"] = args.stages

    ctx = run_pipeline(
        config,
        topic_override=args.topic,
        auto_approve=args.auto_approve,
    )
    print(f"\n완료! 결과: {ctx.work_dir}")
    if ctx.video_url:
        print(f"업로드 URL: {ctx.video_url}")

"""CLI 진입점."""
import argparse
import logging

from youtube_factory.config import load_config
from youtube_factory.pipeline import run_pipeline, MODE_STAGES


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Factory - AI 콘텐츠 자동 생산"
    )
    parser.add_argument("-c", "--config", default="config.yaml", help="설정 파일 경로")
    parser.add_argument("--topic", help="주제 직접 지정")
    parser.add_argument("--auto-approve", action="store_true",
                        help="승인 게이트 건너뜀 (스케줄러/CI용)")
    parser.add_argument("-v", "--verbose", action="store_true")

    # 모드 선택
    parser.add_argument(
        "--mode", default="trending",
        choices=["trending", "cross-lang", "cross-lang-reverse",
                 "platform", "short", "format-cross"],
        help="콘텐츠 전략 모드",
    )

    # 모드별 옵션
    parser.add_argument("--url", nargs="+", help="소스 영상 URL (여러 개 가능)")
    parser.add_argument("--platform", choices=["reddit", "tiktok", "news"],
                        help="플랫폼 (platform 모드)")
    parser.add_argument("--direction", choices=["long2short", "short2long"],
                        default="long2short", help="변환 방향 (short 모드)")
    parser.add_argument("--target-category", help="타겟 카테고리 (format-cross 모드)")
    parser.add_argument("--target-language", default="ko",
                        help="타겟 언어 (cross-lang-reverse 모드, 기본: ko)")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(args.config)

    # 모드가 config의 stages를 오버라이드하도록 stages 키 제거
    if args.mode != "trending":
        config["pipeline"].pop("stages", None)

    ctx = run_pipeline(
        config,
        topic_override=args.topic,
        auto_approve=args.auto_approve,
        mode=args.mode,
        source_urls=args.url or [],
        target_language=args.target_language,
        target_category=args.target_category or "",
        platform=args.platform or "",
        direction=args.direction or "",
    )
    print(f"\n완료! 결과: {ctx.work_dir}")
    if ctx.video_url:
        print(f"업로드 URL: {ctx.video_url}")

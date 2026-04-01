"""Claude Code CLI 래퍼 - Max 요금제 안에서 Claude 호출."""
import logging
import subprocess

log = logging.getLogger(__name__)


def ask_claude(prompt: str, timeout: int = 120) -> str:
    """Claude Code CLI로 프롬프트 전송 후 응답 텍스트 반환.

    Max 요금제 구독 안에서 실행되므로 API 키 불필요.
    """
    result = subprocess.run(
        ["claude", "--print", "--no-input", prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
    )

    if result.returncode != 0:
        log.error(f"Claude CLI 오류: {result.stderr}")
        raise RuntimeError(f"Claude CLI failed: {result.stderr[-300:]}")

    return result.stdout.strip()

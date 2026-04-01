"""YAML 설정 파일 로더."""
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_config(path: str = "config.yaml") -> dict:
    """YAML 설정 로드 + 환경변수 로드."""
    load_dotenv()

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {path}")

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config

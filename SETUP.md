# YouTube Factory 설치 가이드

사무실 PC에서 Claude Code로 바로 실행할 수 있도록 하는 설치 문서.

---

## 1. 사전 요구사항 확인

아래가 설치되어 있어야 합니다.

```bash
# 버전 확인 (모두 통과해야 함)
python --version    # 3.11 이상
node --version      # 18 이상
npm --version       # 9 이상
ffprobe --version   # FFmpeg에 포함
git --version
```

### 없는 경우 설치

| 도구 | 설치 |
|------|------|
| Python 3.11+ | https://www.python.org/downloads/ |
| Node.js 18+ | https://nodejs.org/ |
| FFmpeg | https://www.gyan.dev/ffmpeg/builds/ → ffmpeg-release-essentials.zip 다운 → PATH에 추가 |
| Git | https://git-scm.com/download/win |

---

## 2. 프로젝트 가져오기

```bash
# 방법 A: Git으로 클론 (저장소가 있는 경우)
git clone <저장소URL> D:\dev\youtube-factory
cd D:\dev\youtube-factory

# 방법 B: 폴더 통째로 복사
# 이 PC의 D:\dev\youtube-factory\ 폴더를 USB나 네트워크로 복사
# ※ node_modules 폴더는 복사 안 해도 됨 (3단계에서 설치)
```

---

## 3. 의존성 설치

### Python 의존성

```bash
cd D:\dev\youtube-factory

# 가상환경 생성 + 활성화
python -m venv .venv
.venv\Scripts\activate

# 패키지 설치
pip install -e .
```

### Remotion (Node.js) 의존성

```bash
cd D:\dev\youtube-factory\remotion
npm install
cd ..
```

---

## 4. API 키 설정

`.env` 파일을 프로젝트 루트에 생성합니다.

```bash
copy .env.example .env
```

`.env` 파일을 열어서 API 키를 입력합니다:

```env
# ===== 필수 =====
ANTHROPIC_API_KEY=sk-ant-여기에입력
GOOGLE_API_KEY=AIza여기에입력

# ===== 권장 (주제 수집 품질 향상) =====
YOUTUBE_API_KEY=AIza여기에입력

# ===== 선택 (없으면 자동 스킵) =====
NAVER_CLIENT_ID=여기에입력
NAVER_CLIENT_SECRET=여기에입력
REDDIT_CLIENT_ID=여기에입력
REDDIT_CLIENT_SECRET=여기에입력
REDDIT_USER_AGENT=youtube-factory/0.1
```

### API 키 발급 방법

| 키 | 발급처 | 용도 |
|----|--------|------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/ → API Keys | 주제 선정, 스크립트 생성 |
| `GOOGLE_API_KEY` | https://aistudio.google.com/apikey | Gemini 이미지 생성 |
| `YOUTUBE_API_KEY` | Google Cloud Console → APIs → YouTube Data API v3 활성화 → 사용자 인증정보 | 유튜브 트렌딩 수집 |
| `NAVER_CLIENT_ID/SECRET` | https://developers.naver.com/ → 애플리케이션 등록 → 검색 API + DataLab API | 네이버 트렌드 수집 |
| `REDDIT_CLIENT_ID/SECRET` | https://www.reddit.com/prefs/apps → create app → script 유형 | 레딧 트렌드 수집 |

---

## 5. 설치 확인

```bash
cd D:\dev\youtube-factory
.venv\Scripts\activate

# Python 패키지 확인
ytfactory --help

# Remotion 확인
cd remotion && npx remotion --help && cd ..
```

정상이면 아래와 같이 나옵니다:

```
usage: ytfactory [-h] [-c CONFIG] [--stages STAGES [STAGES ...]] [--topic TOPIC] [--auto-approve] [-v]
YouTube Factory - AI 콘텐츠 자동 생산
```

---

## 6. 실행

### 기본 실행 (승인 게이트 포함)

```bash
cd D:\dev\youtube-factory
.venv\Scripts\activate
ytfactory
```

파이프라인이 실행되면:

1. 트렌딩 데이터 수집 (YouTube, Google Trends, 네이버, Reddit)
2. AI가 주제 선정
3. **🔒 주제 승인 대기** → `y` 승인 / `r` 재생성 / `e` 수정 / `q` 중단
4. 스크립트 생성 (Claude)
5. 음성 생성 (edge-tts)
6. 이미지 생성 (Gemini)
7. 영상 렌더링 (Remotion)
8. 썸네일 생성
9. 소재 내보내기 (CapCut용 폴더)
10. **🔒 최종 승인 대기** → `y` 승인 / `o` 영상 열기 / `f` 소재 폴더 열기 / `q` 중단

### 주제 직접 지정

```bash
ytfactory --topic "AI가 바꾸는 미래 교육"
```

### 특정 스테이지만 실행

```bash
ytfactory --stages topic script
```

### 무인 실행 (승인 게이트 스킵)

```bash
ytfactory --auto-approve
```

### 디버그 모드

```bash
ytfactory -v
```

---

## 7. 출력 결과

실행 완료 후 `output/run_XXXXXXXXXX/` 폴더에 결과물이 생성됩니다:

```
output/run_1711234567/
├── voice_000.mp3 ~ voice_011.mp3   # 장면별 음성
├── visual_000.png ~ visual_011.png  # 장면별 이미지
├── final_video.mp4                  # 최종 영상
├── thumbnail.png                    # 썸네일
├── remotion_props.json              # Remotion 렌더링 데이터
└── capcut_assets/                   # CapCut 편집용 소재
    ├── 00_안녕하세요_오늘은/
    │   ├── voice.mp3
    │   ├── image.png
    │   └── narration.txt
    ├── 01_첫번째_주제는/
    │   ├── voice.mp3
    │   ├── image.png
    │   └── narration.txt
    ├── ...
    ├── script.txt                   # 전체 스크립트
    ├── timeline.txt                 # 타임라인 가이드
    └── metadata.json                # 메타데이터
```

---

## 8. config.yaml 주요 설정

설정을 변경하려면 `config.yaml`을 수정합니다:

```yaml
# 카테고리 변경
topic:
  category: "finance"    # tech, finance, health, education, entertainment, lifestyle

# 영상 길이 변경
script:
  target_duration_seconds: 300   # 5분

# 음성 변경
voice:
  voice_name: "ko-KR-InJoonNeural"   # 남성 음성
  rate: "+10%"                        # 약간 빠르게

# 자막 비활성화
assembly:
  subtitle_enabled: false

# 장면 전환 변경
assembly:
  transition_type: "slide"   # fade, slide, wipe, none

# BGM 추가
assembly:
  bgm_file: "./bgm/chill_music.mp3"
  bgm_volume: 0.3
```

---

## 9. Claude Code에서 실행

사무실 PC에서 Claude Code를 열고:

```
# 프로젝트 디렉토리로 이동
cd D:\dev\youtube-factory

# Claude Code에서 직접 실행 요청
! .venv\Scripts\activate && ytfactory
```

또는 Claude Code에게:

> "youtube-factory 실행해줘"

라고 말하면 됩니다.

---

## 10. 트러블슈팅

### `ytfactory` 명령이 안 되는 경우

```bash
# 가상환경 활성화 확인
.venv\Scripts\activate
# 재설치
pip install -e .
```

### Remotion 렌더링 실패

```bash
# Remotion 재설치
cd remotion
npm install
# Remotion 단독 테스트
npx remotion --help
```

### edge-tts 오류

```bash
# edge-tts 재설치
pip install --upgrade edge-tts
```

### Gemini 이미지 생성 실패

이미지 생성이 실패해도 파이프라인은 중단되지 않습니다 (플레이스홀더로 대체).
`GOOGLE_API_KEY`가 올바른지 확인하세요.

### API 키가 없는 수집기

수집기는 API 키가 없으면 자동 스킵됩니다. 최소한 `ANTHROPIC_API_KEY`만 있으면 파이프라인은 동작합니다 (Claude 단독 모드).

---

## 파이프라인 전체 흐름도

```
                    ┌─ YouTube API (KR/US)
                    ├─ Google Trends
  자료수집 (병렬) ──┼─ 네이버 DataLab
                    └─ Reddit

       ↓ 스코어링 + Claude 분석

  주제 선정 ──→ 🔒 승인 게이트 1 (y/r/e/q)

       ↓

  스크립트 생성 (Claude) ──→ 장면별 나레이션 + 이미지 프롬프트

       ↓ (병렬 가능)

  음성 (edge-tts) + 이미지 (Gemini)

       ↓

  영상 렌더링 (Remotion) ──→ 자막 + 전환효과 + 켄번즈

       ↓

  썸네일 + 소재 내보내기 ──→ 🔒 승인 게이트 2 (y/o/f/q)

       ↓

  YouTube 업로드 (선택)
```

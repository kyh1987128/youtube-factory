# YouTube Factory 설치 및 사용 가이드

사무실 PC에서 Claude Code로 바로 실행할 수 있도록 하는 설치 문서.
GitHub: https://github.com/kyh1987128/youtube-factory

---

## 1. 사전 요구사항

```bash
# 버전 확인 (모두 통과해야 함)
python --version    # 3.11 이상
node --version      # 18 이상
npm --version       # 9 이상
ffprobe --version   # FFmpeg에 포함
git --version
claude --version    # Claude Code CLI
```

### 없는 경우 설치

| 도구 | 설치 |
|------|------|
| Python 3.11+ | https://www.python.org/downloads/ |
| Node.js 18+ | https://nodejs.org/ |
| FFmpeg | https://www.gyan.dev/ffmpeg/builds/ → ffmpeg-release-essentials.zip → PATH에 추가 |
| Git | https://git-scm.com/download/win |
| Claude Code | `npm install -g @anthropic-ai/claude-code` → `claude login` (Max 요금제) |

---

## 2. 설치 (5단계)

```bash
# 1. 클론
git clone https://github.com/kyh1987128/youtube-factory.git D:\dev\youtube-factory
cd D:\dev\youtube-factory

# 2. Python 가상환경 + 패키지
python -m venv .venv
.venv\Scripts\activate
pip install -e .

# 3. Remotion (Node.js)
cd remotion && npm install && cd ..

# 4. API 키 (.env 파일 생성)
copy .env.example .env
# .env 파일 열어서 GOOGLE_API_KEY 입력 (Gemini 이미지 생성용)
# 유일한 필수 키: https://aistudio.google.com/apikey 에서 발급

# 5. Claude Code 로그인 (이미 되어있으면 건너뛰기)
claude login
```

---

## 3. 실행 확인

```bash
cd D:\dev\youtube-factory
.venv\Scripts\activate
ytfactory --help
```

---

## 4. 6가지 모드 사용법

### 모드 1: trending (기본) - 트렌딩 기반 신규 생성

```bash
ytfactory
ytfactory --topic "AI가 바꾸는 미래 교육"    # 주제 직접 지정
```

흐름:
```
트렌딩 웹 검색 → 주제 선정 → 🔒승인 → 스크립트 → 음성 → 이미지 → 영상 → 🔒승인
```

---

### 모드 2: cross-lang - 외국 인기 영상 → 한국어 변형

```bash
# URL 직접 지정
ytfactory --mode cross-lang --url "https://youtube.com/watch?v=xxx"

# 자동 탐색 (Claude가 해외 인기 영상 검색)
ytfactory --mode cross-lang
```

흐름:
```
해외 영상 탐색/지정 → 대본 추출 → 구조 분석 → 한국 문화 변형 → 🔒승인 → 영상 제작 → 🔒승인
```

---

### 모드 3: cross-lang-reverse - 한국 인기 영상 → 외국어 변형

```bash
ytfactory --mode cross-lang-reverse --url "https://youtube.com/watch?v=xxx"
ytfactory --mode cross-lang-reverse --url "https://youtube.com/watch?v=xxx" --target-language en
```

---

### 모드 4: platform - 다른 플랫폼 바이럴 → 유튜브 영상

```bash
ytfactory --mode platform --platform reddit
ytfactory --mode platform --platform tiktok
ytfactory --mode platform --platform news
```

흐름:
```
Reddit/TikTok/뉴스 바이럴 탐색 → 콘텐츠 분석 → 유튜브 롱폼 확장 → 🔒승인 → 영상 제작 → 🔒승인
```

---

### 모드 5: short - 롱폼 ↔ 숏폼 전환

```bash
# 롱폼 → 숏폼 클립 (30~60초 x 3~5개)
ytfactory --mode short --direction long2short --url "https://youtube.com/watch?v=xxx"

# 숏폼 여러 개 → 롱폼 종합
ytfactory --mode short --direction short2long --url "URL1" "URL2" "URL3"
```

---

### 모드 6: format-cross - 포맷 크로스

다른 영상의 형식(구조/전개/톤)을 가져와서 다른 카테고리에 적용.

```bash
# 범죄다큐 형식 → 기업 몰락 스토리
ytfactory --mode format-cross --url "https://youtube.com/watch?v=xxx" --target-category "기업 몰락"

# 랭킹 영상 형식 → 테크 카테고리
ytfactory --mode format-cross --url "https://youtube.com/watch?v=xxx" --target-category "tech"
```

흐름:
```
소스 영상 대본 추출 → 형식/구조만 분석 → 타겟 카테고리에 적용 → 🔒승인 → 영상 제작 → 🔒승인
```

---

## 5. 공통 옵션

```bash
ytfactory --auto-approve    # 승인 게이트 건너뜀 (무인 실행)
ytfactory -v                # 디버그 모드
ytfactory -c my_config.yaml # 다른 설정 파일 사용
```

---

## 6. 승인 게이트

모든 모드에 승인 게이트 2개가 있습니다:

### 게이트 1: 주제/변형 승인 (제작 전)
```
[y] 승인     - 진행
[r] 재생성   - 다시 뽑기
[e] 수정     - 제목/설명 직접 수정
[q] 중단     - 파이프라인 중단
```

### 게이트 2: 최종 영상 승인 (제작 후)
```
[y] 승인     - 완료 (또는 업로드)
[o] 열기     - 영상 파일 열기
[f] 폴더     - 소재 폴더 열기 (CapCut 편집용)
[q] 중단     - 중단 (소재는 보존)
```

---

## 7. 출력 결과

```
output/run_XXXXXXXXXX/
├── voice_000.mp3 ~ voice_011.mp3   # 장면별 음성
├── visual_000.png ~ visual_011.png  # 장면별 이미지 (Gemini)
├── final_video.mp4                  # 최종 영상 (Remotion)
├── thumbnail.png                    # 썸네일
├── remotion_props.json              # 렌더링 데이터
└── capcut_assets/                   # CapCut 편집용 소재
    ├── 00_장면제목/
    │   ├── voice.mp3
    │   ├── image.png
    │   └── narration.txt
    ├── ...
    ├── script.txt
    ├── timeline.txt
    └── metadata.json
```

---

## 8. config.yaml 주요 설정

```yaml
# 카테고리 변경
topic:
  category: "finance"    # tech, finance, health, education, entertainment, lifestyle

# 영상 길이
script:
  target_duration_seconds: 300   # 5분

# 음성 변경
voice:
  voice_name: "ko-KR-InJoonNeural"   # 남성 음성
  rate: "+10%"                        # 약간 빠르게

# 자막/전환/켄번즈
assembly:
  subtitle_enabled: true
  transition_type: "fade"      # fade, slide, wipe, none
  ken_burns: true

# BGM
assembly:
  bgm_file: "./bgm/chill_music.mp3"
  bgm_volume: 0.3
```

---

## 9. Claude Code에서 실행

```
cd D:\dev\youtube-factory
! .venv\Scripts\activate && ytfactory --mode cross-lang
```

또는 Claude Code에게:
> "youtube-factory cross-lang 모드로 실행해줘"

---

## 10. 트러블슈팅

| 문제 | 해결 |
|------|------|
| `ytfactory` 명령 안 됨 | `.venv\Scripts\activate` 후 `pip install -e .` |
| Remotion 렌더링 실패 | `cd remotion && npm install` |
| edge-tts 오류 | `pip install --upgrade edge-tts` |
| Gemini 이미지 실패 | 파이프라인 중단 안 됨 (플레이스홀더 대체). `.env`의 GOOGLE_API_KEY 확인 |
| Claude CLI 오류 | `claude login`으로 재인증 |

---

## 전체 아키텍처

```
Python (파이프라인 오케스트레이터)
├── topic.py      → Claude Code 웹 검색으로 주제 선정
├── transcript.py  → Claude Code로 대본 추출
├── analyze.py     → Claude Code로 구조/인기 요인 분석
├── adapt.py       → Claude Code로 문화/언어/포맷 변형
├── script.py      → Claude Code로 장면별 스크립트 생성
├── voice.py       → edge-tts (무료 TTS)
├── visuals.py     → Gemini API (AI 이미지 생성)
├── assembly.py    → Remotion (Node.js 영상 렌더링)
├── thumbnail.py   → Pillow (썸네일 생성)
├── export.py      → CapCut용 소재 내보내기
└── upload.py      → YouTube Data API (업로드)

필요한 키: GOOGLE_API_KEY 1개
나머지: Claude Code Max 요금제 안에서 실행
```

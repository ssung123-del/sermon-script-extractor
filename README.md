# 📜 유튜브 설교 스크립트 추출기 (YouTube Sermon Script Extractor)

유튜브 재생목록(Playlist)에 포함된 수백 개의 "설교 영상"에서 **자막만 빠르고 깔끔하게 추출**하여, 옵시디언(Obsidian)이나 노트북LM(NotebookLM) 등에서 활용하기 좋은 텍스트 자산으로 일괄 변환해 주는 Streamlit 기반 웹 애플리케이션입니다.

## 🌟 주요 기능 (Key Features)

- **초고속 메타데이터 분석**: 영상 파일을 다운로드하지 않고 yt-dlp를 이용해 재생목록 구조와 자막(vtt)만 병렬로 빠르게 가져옵니다.
- **자막 중복 문구(Overlap) 완벽 제거**: 유튜브 자동 생성 자막 특유의 "이전 문장 끝과 다음 문장 시작이 겹치는 현상(Suffix-Prefix Overlap)"을 알고리즘으로 계산해 매끄럽게 병합합니다.
- **정교한 텍스트 클리닝**: 타임스탬프(`00:00:01.234 -->`), HTML 태그, 소음 표기(`[음악]`, `[박수]`), 불필요한 특수문자를 정규표현식으로 모두 제거하여 순도 100%의 깔끔한 텍스트만 남깁니다.
- **중단 및 저장 (Stop & Save)**: 수백 개가 넘는 대량의 영상을 추출하다가 중간에 언제든 "⏹ 정지" 버튼을 누르면, 지금까지 안전하게 추출된 자막들만 모아서 즉시 ZIP 파일로 묶어줍니다.
- **Apple 스타일 미니멀 UX**: Inter / San Francisco 폰트 기반의 세련된 다크 모드 UI와 직관적인 실시간 진행률 스탯 창을 제공합니다.

---

## 🚀 시작하기 (Getting Started)

### 1단계: 로컬에서 실행하기 (Local Run)

파이썬(Python) 3.10 이상이 설치되어 있어야 합니다.

```bash
# 1. 레포지토리 클론
git clone https://github.com/ssung123-del/sermon-script-extractor.git
cd sermon-script-extractor

# 2. 패키지 설치
pip install -r requirements.txt

# 3. Streamlit 서버 실행
streamlit run app.py
```

브라우저가 열리며 `http://localhost:8501`에서 앱이 실행됩니다.

### 2단계: 웹에 무료 배포하기 (Deploy to Web)

이 레포지토리는 [Streamlit Community Cloud](https://share.streamlit.io/)에 최적화되어 있습니다.
1. Streamlit Community Cloud에 가입 및 로그인
2. "New app" 클릭
3. Repository 칸에 `ssung123-del/sermon-script-extractor` 연결
4. Main file path 칸에 `app.py` 입력
5. "Deploy!" 클릭 🎈

---

## 🛠️ 기술 스택 (Tech Stack)
- **Frontend / Backend**: [Streamlit](https://streamlit.io/) (단일 Python 스크립트로 풀스택 구현)
- **Core Engine**: [yt-dlp](https://github.com/yt-dlp/yt-dlp) (유튜브 데이터 추출)
- **Data Processing**: Python 내장 `re` (정규표현식), `tempfile`, `zipfile`

---

## 💡 활용 팁 (Tips)
다운로드된 **`[순번] - [YYYYMMDD] - [영상제목].txt`** 포맷의 텍스트 파일들을 그대로 복사하여 
- **노트북LM (NotebookLM)** 에 소스로 집어넣어 "이 목사님의 2024년도 주요 설교 키워드와 주제를 요약해 줘"라고 질문해 보세요.
- **옵시디언 (Obsidian)** 폴더에 넣어 마크다운(Markdown) 문서로 관리하며 나만의 제텔카스텐(Zettelkasten) 성경 노트를 구성해 보세요.

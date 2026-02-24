"""
유튜브 설교 스크립트 일괄 추출 웹 앱
=====================================
유튜브 재생목록의 모든 영상에서 자동 생성 한국어 자막을 추출하여
클리닝된 텍스트 파일(.txt)로 변환하고, ZIP으로 일괄 다운로드합니다.

기술 스택: Python, Streamlit, yt-dlp, re, zipfile
"""

import logging
import os
import random
import re
import shutil
import tempfile
import time
import zipfile
from datetime import datetime
from typing import Optional

import streamlit as st
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

# ──────────────────────────────────────────────
# 로깅 설정
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. CONFIGURATION — 페이지 설정 & 다크 모드 CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def setup_page() -> None:
    """Streamlit 페이지 초기 설정 및 Apple 스타일 다크 모드 CSS 주입."""
    st.set_page_config(
        page_title="설교 스크립트 추출기",
        page_icon="📜",
        layout="centered",
    )

    # Apple 미니멀 다크 모드 CSS
    st.markdown("""
    <style>
        /* ── 전역 다크 테마 ── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        .stApp {
            background-color: #0D1117;
            color: #F0F6FC;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display',
                         'Segoe UI', Roboto, sans-serif;
        }

        /* ── 헤더 영역 ── */
        .main-header {
            text-align: center;
            padding: 2.5rem 0 1rem 0;
        }
        .main-header h1 {
            font-size: 2rem;
            font-weight: 700;
            color: #F0F6FC;
            letter-spacing: -0.02em;
            margin-bottom: 0.25rem;
        }
        .main-header p {
            font-size: 0.95rem;
            color: #8B949E;
            font-weight: 300;
        }

        /* ── 입력 영역 스타일 ── */
        .stTextInput > div > div > input {
            background-color: #161B22 !important;
            border: 1px solid #30363D !important;
            border-radius: 12px !important;
            color: #F0F6FC !important;
            padding: 0.75rem 1rem !important;
            font-size: 0.95rem !important;
            font-family: 'Inter', sans-serif !important;
            transition: border-color 0.2s ease;
        }
        .stTextInput > div > div > input:focus {
            border-color: #1F6FEB !important;
            box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.15) !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: #484F58 !important;
        }

        /* ── 버튼 스타일 ── */
        .stButton > button {
            background: linear-gradient(135deg, #1F6FEB, #1A5BC4) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.7rem 2rem !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            letter-spacing: -0.01em;
            width: 100%;
            transition: all 0.2s ease !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #388BFD, #1F6FEB) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(31, 111, 235, 0.3) !important;
        }
        .stButton > button:active {
            transform: translateY(0);
        }

        /* ── 다운로드 버튼 ── */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #238636, #1B6E2D) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.7rem 2rem !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            width: 100%;
            transition: all 0.2s ease !important;
        }
        .stDownloadButton > button:hover {
            background: linear-gradient(135deg, #2EA043, #238636) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(35, 134, 54, 0.3) !important;
        }

        /* ── 중단 버튼 (Stop) ── */
        div[data-testid="stButton"] > button:has(+ div > div > span:contains("정지")) {
            background: linear-gradient(135deg, #F85149, #DA3633) !important;
            color: #FFFFFF !important;
        }
        div[data-testid="stButton"] > button:has(+ div > div > span:contains("정지")):hover {
            background: linear-gradient(135deg, #FF6A69, #F85149) !important;
            box-shadow: 0 4px 16px rgba(248, 81, 73, 0.3) !important;
        }

        /* ── 진행 상태 영역 ── */
        .status-card {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 12px;
            padding: 1.25rem;
            margin: 0.75rem 0;
        }
        .status-card .label {
            font-size: 0.75rem;
            color: #8B949E;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }
        .status-card .value {
            font-size: 1rem;
            color: #F0F6FC;
            font-weight: 500;
        }

        /* ── 결과 통계 카드 ── */
        .result-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            margin: 1rem 0;
        }
        .stat-card {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }
        .stat-card .number {
            font-size: 2.25rem;
            font-weight: 700;
            letter-spacing: -0.03em;
        }
        .stat-card .description {
            font-size: 0.8rem;
            color: #8B949E;
            margin-top: 0.25rem;
            font-weight: 400;
        }
        .stat-success .number { color: #3FB950; }
        .stat-fail .number { color: #F85149; }

        /* ── 프로그레스 바 커스텀 ── */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #1F6FEB, #388BFD) !important;
            border-radius: 8px !important;
        }
        .stProgress > div > div > div {
            background-color: #21262D !important;
            border-radius: 8px !important;
        }

        /* ── 알림 영역 ── */
        .stAlert {
            background-color: #161B22 !important;
            border-radius: 12px !important;
        }

        /* ── Streamlit 기본 요소 숨기기 ── */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }

        /* ── 구분선 ── */
        hr {
            border-color: #21262D !important;
            margin: 1.5rem 0 !important;
        }

        /* ── 푸터 ── */
        .app-footer {
            text-align: center;
            padding: 2rem 0 1rem 0;
            font-size: 0.75rem;
            color: #484F58;
        }
    </style>
    """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. CORE LOGIC — yt-dlp 자막 추출 & 데이터 처리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_playlist_entries(url: str) -> list[dict]:
    """
    재생목록 URL에서 모든 영상의 메타데이터를 추출한다.

    왜: 실제 영상을 다운로드하지 않고 메타데이터(제목, 날짜, ID)만
    가져와 메모리를 절약하고 속도를 높이기 위함.

    Returns:
        list[dict]: 각 영상의 {id, title, upload_date, url} 목록
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",  # 재생목록 메타데이터만 초고속 추출
        "ignoreerrors": True,           # 비공개 영상 등 에러 무시
        "skip_download": True,
        "dump_single_json": True,
    }

    entries = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        if info is None:
            logger.error("URL에서 정보를 추출할 수 없습니다.")
            return entries

        # 재생목록인 경우 entries 필드에 영상 목록이 존재
        raw_entries = info.get("entries", [info])

        for idx, entry in enumerate(raw_entries, start=1):
            if entry is None:
                # 비공개이거나 삭제된 영상은 None으로 반환됨
                logger.warning(f"[{idx}] 접근 불가능한 영상 건너뜀")
                continue

            entries.append({
                "index": idx,
                "id": entry.get("id", "unknown"),
                "title": entry.get("title", "제목없음"),
                "upload_date": entry.get("upload_date", "00000000"),
                "url": entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id', '')}",
            })

    logger.info(f"재생목록에서 {len(entries)}개 영상 메타데이터 추출 완료")
    return entries


def extract_subtitle(video_id: str) -> Optional[str]:
    """
    youtube-transcript-api를 사용하여 개별 영상의 자막 텍스트를 추출한다.

    왜: yt-dlp는 영상 전체 페이지를 파싱하여 자막을 가져오는 무거운 방식이라
    클라우드 환경에서 HTTP 429 차단이 빈번했다.
    youtube-transcript-api는 자막 전용 API를 직접 호출하는 경량 라이브러리로,
    요청이 훨씬 가볍고 빠르며 차단 위험이 낮다.

    Args:
        video_id: 유튜브 영상 ID (예: 'dQw4w9WgXcQ')

    Returns:
        추출된 자막 텍스트 또는 None (자막 없는 경우)
    """
    try:
        api = YouTubeTranscriptApi()
        # 한국어 자막 우선, 없으면 영어 자막 fallback
        transcript = api.fetch(video_id, languages=["ko", "en"])

        # 자막 스니펫들을 단일 텍스트로 병합
        text_parts = [snippet.text for snippet in transcript.snippets]
        return " ".join(text_parts)

    except (NoTranscriptFound, TranscriptsDisabled):
        logger.warning(f"자막 없음 또는 비활성화됨: {video_id}")
        return None
    except VideoUnavailable:
        logger.warning(f"영상 접근 불가: {video_id}")
        return None
    except Exception as e:
        logger.error(f"자막 추출 실패 [{video_id}]: {e}")
        return None


def parse_vtt_lines(vtt_content: str) -> list[str]:
    """
    VTT 형식의 자막 텍스트에서 순수 텍스트 라인만 추출한다.

    왜: VTT에는 헤더, 타임스탬프, 빈 줄 등 불필요한 메타 정보가
    포함되어 있어 텍스트만 분리해야 한다.
    """
    lines = []
    for line in vtt_content.strip().split("\n"):
        line = line.strip()

        # VTT 헤더, 빈 줄, 타임스탬프 라인 건너뛰기
        if not line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if line.startswith("NOTE"):
            continue
        # 타임스탬프 라인: "00:00:01.234 --> 00:00:03.456"
        if re.match(r"\d{2}:\d{2}:\d{2}\.\d{3}\s*-->", line):
            continue
        # 순수 숫자만 있는 줄 (큐 인덱스)
        if re.match(r"^\d+$", line):
            continue

        lines.append(line)

    return lines


def remove_duplicate_lines(lines: list[str]) -> str:
    """
    유튜브 자막 특유의 문장 겹침 현상을 해결한다.

    왜: 유튜브 자동 자막은 이전 프레임의 텍스트 끝부분이 다음
    프레임의 시작 부분에 중복되어 나타나는 특성이 있다.
    suffix-prefix overlap을 계산하여 중복 구간을 제거하고 병합한다.

    알고리즘:
        1. 이전 라인의 suffix와 현재 라인의 prefix가 겹치는 최대 길이를 계산
        2. 겹치는 부분을 제거한 나머지만 결과에 추가
        3. 완전히 동일한 줄은 건너뜀
    """
    if not lines:
        return ""

    result = lines[0]
    prev_line = lines[0]

    for curr_line in lines[1:]:
        # 완전히 동일한 줄은 건너뛰기
        if curr_line == prev_line:
            continue

        # 이전 줄의 suffix와 현재 줄의 prefix 간 최대 겹침 길이 계산
        overlap_len = _find_overlap(prev_line, curr_line)

        if overlap_len > 0:
            # 겹치는 부분을 제외한 새로운 텍스트만 추가
            new_part = curr_line[overlap_len:]
            if new_part.strip():
                result += new_part
        else:
            # 겹치지 않으면 공백 하나를 두고 이어붙이기
            result += " " + curr_line

        prev_line = curr_line

    return result


def _find_overlap(prev: str, curr: str) -> int:
    """
    prev의 suffix와 curr의 prefix가 겹치는 최대 길이를 반환한다.

    왜: 유튜브 자막의 중복 패턴은 이전 줄의 끝부분이 다음 줄의
    시작부분과 동일한 경우이므로, 가장 긴 suffix-prefix 매칭을 찾는다.
    """
    max_overlap = min(len(prev), len(curr))
    best = 0

    for i in range(1, max_overlap + 1):
        if prev[-i:] == curr[:i]:
            best = i

    return best


def clean_text(raw: str) -> str:
    """
    자막 텍스트에서 불필요한 요소를 제거하여 순수 텍스트로 변환한다.

    왜: 노트북LM/Obsidian에서 활용하려면 타임스탬프, 태그,
    소음 표기 등이 없는 깨끗한 텍스트가 필요하다.

    제거 대상:
        - HTML 태그: <b>, <i>, <font> 등
        - 타임스탬프: 00:00:01.234 형식
        - 소음 표기: [음악], [박수], [웃음], [Music] 등
        - HTML 엔티티: &nbsp; &amp; 등
        - 연속 공백 및 불필요한 줄바꿈
    """
    # 1) HTML 태그 제거 — 자막에 포함된 <font>, <c.colorXXXXXX> 등
    text = re.sub(r"<[^>]+>", "", raw)

    # 2) 타임스탬프 제거 — "00:01:23.456" 형식
    text = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3}", "", text)

    # 3) 소음/이벤트 표기 제거 — [음악], [박수], [웃음], [Music], [Applause] 등
    text = re.sub(r"\[[\w\s]+\]", "", text)

    # 4) HTML 엔티티 제거
    text = re.sub(r"&\w+;", " ", text)

    # 5) 화살표(-->) 잔여물 제거 (타임스탬프 구분자)
    text = re.sub(r"-->", "", text)

    # 6) 특수문자 정리 — 괄호, 연속 기호 등 제거 (한글/영문/숫자/기본구두점 보존)
    text = re.sub(r"[^\w\s가-힣a-zA-Z0-9.,!?·\-~()\"'。，！？]", "", text)

    # 7) 연속 공백을 단일 공백으로
    text = re.sub(r"[ \t]+", " ", text)

    # 8) 연속 줄바꿈을 단일 줄바꿈으로
    text = re.sub(r"\n{2,}", "\n", text)

    # 9) 각 줄 앞뒤 공백 제거 및 빈 줄 제거
    cleaned_lines = [line.strip() for line in text.split("\n") if line.strip()]

    return "\n".join(cleaned_lines)


def build_filename(index: int, upload_date: str, title: str) -> str:
    """
    출력 파일명을 규칙에 맞게 생성한다.

    왜: 일관된 파일명 규칙(`[순번] - [YYYYMMDD] - [제목].txt`)은
    파일 정렬과 검색을 쉽게 만들어 Obsidian 등에서의 활용성을 높인다.

    파일 시스템에서 금지된 문자도 제거하여 안전한 파일명을 보장한다.
    """
    # 날짜 포맷 정리 — YYYYMMDD 형식 유지
    if len(upload_date) == 8:
        formatted_date = upload_date
    else:
        formatted_date = "00000000"

    # 파일 시스템에 안전한 제목으로 변환
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    safe_title = safe_title.strip()
    # 너무 긴 제목은 잘라내기 (파일 시스템 제한 고려)
    if len(safe_title) > 100:
        safe_title = safe_title[:100].rstrip()

    # 순번을 3자리 0-패딩으로 (최대 999개 지원)
    padded_index = str(index).zfill(3)

    return f"{padded_index} - {formatted_date} - {safe_title}.txt"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. I/O — 파일 저장 & ZIP 압축
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def save_text_file(content: str, filepath: str) -> None:
    """텍스트 파일을 UTF-8 인코딩으로 저장한다."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def create_zip(source_dir: str, zip_path: str) -> str:
    """
    소스 디렉토리의 모든 .txt 파일을 단일 ZIP으로 압축한다.

    왜: 수백 개의 파일을 개별 다운로드하는 것은 비효율적이므로,
    하나의 ZIP 파일로 묶어 편의성을 높인다.

    Returns:
        생성된 ZIP 파일의 절대 경로
    """
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in sorted(os.listdir(source_dir)):
            if filename.endswith(".txt"):
                filepath = os.path.join(source_dir, filename)
                zf.write(filepath, arcname=filename)

    logger.info(f"ZIP 파일 생성 완료: {zip_path}")
    return zip_path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. PROCESSING — 영상 단위 처리 파이프라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def process_single_video(
    entry: dict,
    output_dir: str,
    subtitle_tmp_dir: str,
) -> dict:
    """
    단일 영상의 자막 추출 → 클리닝 → 저장 파이프라인을 실행한다.

    왜: 개별 영상 처리를 독립 함수로 분리하면, 에러 발생 시
    해당 영상만 건너뛰고 나머지를 계속 처리할 수 있다 (Fault Tolerance).

    Returns:
        dict: {success: bool, title: str, error: str|None}
    """
    title = entry["title"]
    video_id = entry["id"]

    try:
        # 1단계: 자막 추출 (youtube-transcript-api 사용 — 가볍고 빠름)
        raw_subtitle = extract_subtitle(video_id)
        
        if raw_subtitle is None:
            return {
                "success": False,
                "title": title,
                "error": "자막 없음 (자동 자막 미생성 또는 비공개)",
            }

        # 2단계: 클리닝 (이미 텍스트 형태로 받았으므로 VTT 파싱/중복제거 불필요)
        cleaned_text = clean_text(raw_subtitle)
        if not cleaned_text.strip():
            return {
                "success": False,
                "title": title,
                "error": "클리닝 후 텍스트가 비어 있음",
            }

        # 3단계: 파일 저장
        filename = build_filename(
            entry["index"],
            entry.get("upload_date", "00000000"),
            title,
        )
        filepath = os.path.join(output_dir, filename)
        save_text_file(cleaned_text, filepath)

        return {"success": True, "title": title, "error": None}

    except Exception as e:
        # Fault Tolerance — 어떤 예외든 로깅 후 계속 진행
        logger.error(f"영상 처리 실패 [{title}]: {e}")
        return {
            "success": False,
            "title": title,
            "error": str(e),
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. UI COMPONENTS — Streamlit 인터페이스
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_header() -> None:
    """앱 상단 헤더를 렌더링한다."""
    st.markdown("""
    <div class="main-header">
        <h1>📜 설교 스크립트 추출기</h1>
        <p>유튜브 재생목록에서 설교 자막을 일괄 추출합니다</p>
    </div>
    """, unsafe_allow_html=True)


def render_input_section() -> tuple[str, bool]:
    """
    URL 입력 및 시작 버튼을 렌더링한다.

    Returns:
        (입력된 URL, 시작 버튼 클릭 여부)
    """
    url = st.text_input(
        "유튜브 URL",
        placeholder="재생목록 또는 개별 영상 URL을 붙여넣으세요",
        label_visibility="collapsed",
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        start = st.button("✦  추출 시작", use_container_width=True)
    with col2:
        st.markdown(
            '<div style="font-size:0px"><span style="display:none">정지</span></div>',
            unsafe_allow_html=True
        )
        stop = st.button("⏹ 정지", use_container_width=True, key="stop_btn")
        
        if stop:
            st.session_state["stop_requested"] = True
            
    # 시작을 누르면 정지 상태 초기화
    if start:
        st.session_state["stop_requested"] = False

    return url, start


def render_result_summary(success_count: int, fail_count: int, failed_list: list[dict]) -> None:
    """
    작업 완료 후 성공/실패 통계를 시각적으로 표시한다.

    왜: 사용자에게 일목요연한 피드백을 제공하여
    어떤 영상이 실패했는지 빠르게 파악할 수 있게 한다.
    """
    total = success_count + fail_count

    st.markdown(f"""
    <div class="result-grid">
        <div class="stat-card stat-success">
            <div class="number">{success_count}</div>
            <div class="description">성공</div>
        </div>
        <div class="stat-card stat-fail">
            <div class="number">{fail_count}</div>
            <div class="description">실패</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 실패 목록이 있으면 접이식으로 표시
    if failed_list:
        with st.expander(f"⚠️ 실패한 영상 ({fail_count}건)", expanded=False):
            for item in failed_list:
                st.markdown(
                    f"- **{item['title']}** — _{item['error']}_"
                )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. MAIN — 앱 진입점 & 전체 워크플로우 오케스트레이션
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main() -> None:
    """
    Streamlit 앱의 메인 함수.

    전체 워크플로우:
        1. 사용자로부터 유튜브 URL 입력 받기
        2. yt-dlp로 재생목록 메타데이터 초고속 추출 (extract_flat)
        3. 각 영상의 자막 추출 → 클리닝 → 저장 (ThreadPool 병렬 처리)
        4. ZIP 파일 생성 → 다운로드 버튼 제공
        5. 임시 파일 정리
    """
    setup_page()
    render_header()

    st.markdown("---")

    url, start_clicked = render_input_section()

    if start_clicked and url.strip():
        # ── 임시 디렉토리 생성 (Resource Management) ──
        tmp_base = tempfile.mkdtemp(prefix="yt_sermon_")
        output_dir = os.path.join(tmp_base, "scripts")
        subtitle_tmp_dir = os.path.join(tmp_base, "subtitles")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(subtitle_tmp_dir, exist_ok=True)

        try:
            # ── 1단계: 재생목록 분석 ──
            with st.status("🔍 재생목록 분석 중...", expanded=True) as status:
                st.write("영상 목록을 가져오고 있습니다...")
                entries = get_playlist_entries(url.strip())

                if not entries:
                    st.error("⛔ 영상을 찾을 수 없습니다. URL을 확인해 주세요.")
                    return

                st.write(f"✅ **{len(entries)}개** 영상을 발견했습니다.")
                status.update(
                    label=f"✅ {len(entries)}개 영상 발견",
                    state="complete",
                )

            st.markdown("---")

            # ── 2단계: 자막 추출 & 처리 (순차 처리로 롤백 및 안전 대기) ──
            progress_bar = st.progress(0, text="준비 중...")
            status_area = st.empty()
            total = len(entries)
            success_count = 0
            fail_count = 0
            failed_list = []
            
            for i, entry in enumerate(entries):
                # 정지 버튼 확인
                if st.session_state.get("stop_requested", False):
                    st.warning("사용자에 의해 작업이 중단되었습니다. 지금까지 추출된 파일만 저장합니다.")
                    break

                current = i + 1
                progress = current / total
                title = entry["title"]

                # 진행률 UI 업데이트
                progress_bar.progress(
                    progress,
                    text=f"처리 중 ({current}/{total})",
                )
                status_area.markdown(f"""
                <div class="status-card">
                    <div class="label">현재 처리 중</div>
                    <div class="value">{title}</div>
                </div>
                """, unsafe_allow_html=True)

                # 개별 영상 처리 (Fault Tolerance 적용)
                result = process_single_video(entry, output_dir, subtitle_tmp_dir)

                if result["success"]:
                    success_count += 1
                else:
                    fail_count += 1
                    failed_list.append(result)
                
                # ── 429 에러 근본 방지: 영상 사이 직접적 쿨다운 ──
                # 왜: yt-dlp의 sleep_interval은 자막 API 요청에 적용되지 않으므로,
                # 파이썬 코드에서 직접 time.sleep()을 호출해야 한다.
                cooldown = random.uniform(3, 6)  # 3~6초 랜덤 대기
                time.sleep(cooldown)

            # 진행률 완료/중단 표시
            is_stopped = st.session_state.get("stop_requested", False)
            if is_stopped:
                progress_bar.progress(progress, text=f"⏹ 중단됨 ({current}/{total})")
            else:
                progress_bar.progress(1.0, text="✅ 모든 영상 처리 완료!")
                
            status_area.empty()

            st.markdown("---")

            # ── 3단계: 결과 요약 ──
            render_result_summary(success_count, fail_count, failed_list)

            # ── 4단계: ZIP 생성 & 다운로드 ──
            if success_count > 0:
                zip_path = os.path.join(tmp_base, "설교_스크립트.zip")
                create_zip(output_dir, zip_path)

                with open(zip_path, "rb") as f:
                    zip_data = f.read()

                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    label=f"📥  스크립트 다운로드 ({success_count}개 파일)",
                    data=zip_data,
                    file_name=f"설교_스크립트_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    use_container_width=True,
                )
            else:
                st.warning("추출된 스크립트가 없습니다.")

        finally:
            # ── Resource Management: 임시 파일 정리 ──
            # 참고: ZIP 데이터는 이미 메모리에 로드되었으므로 안전하게 삭제 가능
            try:
                shutil.rmtree(tmp_base, ignore_errors=True)
                logger.info(f"임시 디렉토리 정리 완료: {tmp_base}")
            except Exception as e:
                logger.warning(f"임시 디렉토리 정리 실패: {e}")

    elif start_clicked and not url.strip():
        st.warning("URL을 입력해 주세요.")

    # ── 하단 안내 ──
    st.markdown("""
    <div class="app-footer">
        재생목록 URL 또는 개별 영상 URL 모두 지원합니다<br>
        자동 생성 한국어 자막(ko)이 있는 영상만 추출됩니다
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

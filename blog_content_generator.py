"""
웨딩 블로그 글 생성 모듈 (jarvis_core.py 프롬프트 구조 그대로)
- 웨딩홀 이름을 받아서 블로그 제목 + 본문을 생성
- [SECTION_BREAK]로 섹션 구분 (이미지 삽입 포인트)
- 날짜 미포함 (과거 촬영을 포트폴리오로 올리는 용도)
"""
import subprocess
import re


def search_wedding_hall_info(venue_name: str) -> str:
    """웨딩홀 정보를 Claude CLI로 검색 (jarvis_core.py 동일)"""
    prompt = f"""{venue_name} 웨딩홀 공식 정보를 웹에서 검색해서 아래 항목만 팩트로 정리하세요.
검색 키워드: '{venue_name} 웨딩홀 주소 홀 정보'
반드시 검색 결과에 있는 정보만 작성하세요. 없으면 해당 줄 삭제.

[출력 형식 - 이것만 출력]
주소: (도로명 주소)
지하철: (역명 + 출구번호 + 도보/차량 시간)
주차: (주차 가능 대수 또는 정보)
홀이름: (실제 홀 이름 목록)
홀개수: (숫자)
수용인원: (홀별 수용 인원)
특징: (웨딩홀 공식 특징 1~3줄)"""
    try:
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True, text=True, timeout=60, cwd="/tmp",
        )
        if result.returncode != 0:
            return ""
        lines = []
        for line in result.stdout.strip().split("\n"):
            if "정보없음" not in line and "없음" not in line and line.strip():
                lines.append(line)
        return "\n".join(lines).strip()
    except Exception as e:
        print(f"웨딩홀 검색 오류: {e}")
        return ""


def generate_wedding_blog(venue_name: str, num_photos: int = 30) -> dict:
    """
    웨딩 촬영 블로그 글을 생성합니다. (jarvis_core.py 프롬프트 구조 그대로)

    Args:
        venue_name: 웨딩홀 이름 (예: "영등포JK아트컨벤션")
        num_photos: 업로드할 사진 수

    Returns:
        {"title": "...", "content": "...(SECTION_BREAK 포함)"}
    """
    # 1단계: 웨딩홀 정보 검색
    print(f"🔍 {venue_name} 정보 검색 중...")
    hall_info = search_wedding_hall_info(venue_name)
    if hall_info:
        print(f"✅ 검색 완료!\n{hall_info}")
    else:
        print("⚠️ 검색 정보 없음 - 수치 언급 없이 작성")

    # 2단계: 글 생성 (jarvis_core.py 마리안웨딩 프롬프트 그대로)
    prompt = f"""너는 지금 네이버 블로그 글을 쓰는 작가다. 아래 규칙을 100% 따라라.

[필수 출력 규칙 - 위반 절대 금지]
1. 응답의 첫 줄은 반드시 "TITLE: " 으로 시작
2. TITLE: 앞에 어떤 텍스트도 절대 쓰지 마라 (인사, 안내, 설명 전부 금지)
3. [제목], ---,  ## 등 다른 형식 일절 금지
4. 이모지, 마크다운 금지
5. 제목에 마리안웨딩 포함 금지

[글 정보]
브랜드: 마리안웨딩 / 웨딩홀: {venue_name}
검색 정보: {hall_info if hall_info else "확인된 정보 없음 - 수치 언급 금지"}
분량: 공백 제외 1500자 이상
SEO: '{venue_name}' 키워드 최소 7회 자연스럽게 포함

[출력 형식]
TITLE: {venue_name} 본식스냅 - [웨딩홀의 촬영 경험을 고급스럽게 어필하는 창의적 문구. 예: "수백 번 찍어보고 알게 된 것들" / "촬영작가만 아는 그 공간의 빛" / "직접 촬영하고 나서야 보인 것들"]

안녕하세요 마리안웨딩입니다.
[SECTION_BREAK]
위치와 오시는 방법 (검색 정보 기반. 3~4문장)
[SECTION_BREAK]
{venue_name} 공간 특징 (홀 이름, 조명, 버진로드. 4~5문장)
[SECTION_BREAK]
직접 촬영하며 알게 된 것들 (황금 시간대, 포인트 장면. 4~5문장)
[SECTION_BREAK]
장점과 주의할 점 (3~4문장)
[SECTION_BREAK]
마무리 (마지막 문장: 더 궁금하신 점은 마리안웨딩 카카오채널로 편하게 문의해 주세요. http://pf.kakao.com/_Xzmwn)"""

    try:
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True, text=True, timeout=500, cwd="/tmp",
        )
        if result.returncode != 0:
            print(f"Claude CLI 오류: {result.stderr}")
            return None
        raw = result.stdout.strip()
    except FileNotFoundError:
        print("Claude CLI를 찾을 수 없습니다.")
        return None
    except subprocess.TimeoutExpired:
        print("Claude CLI 타임아웃.")
        return None

    # TITLE: 파싱 (jarvis_core.py 동일 로직)
    raw = re.sub(r"[\U00010000-\U0010ffff]", "", raw)
    raw = re.sub(r"^#+\s*", "", raw, flags=re.MULTILINE)
    raw = re.split(r"\n\s*(?:Sources?:|출처:|참고:)", raw, flags=re.IGNORECASE)[0].strip()

    title = f"{venue_name} 본식스냅 후기"
    titles_found = re.findall(r"(?:TITLE:|\[제목\]:?)\s*(.+)", raw)
    if titles_found:
        title = titles_found[-1].strip().replace("[", "").replace("]", "").replace("#", "").replace("*", "")
    if venue_name not in title:
        title = f"{venue_name} {title}"

    blog_content = re.sub(r"^[\s\S]*(?:TITLE:|\[제목\]:?)[^\n]*\n?", "", raw).strip()
    if blog_content.startswith("[SECTION_BREAK]"):
        blog_content = blog_content.replace("[SECTION_BREAK]", "", 1).strip()

    blog_content = re.split(r"\n\s*(?:Sources?:|출처:|참고:|References?:)", blog_content, flags=re.IGNORECASE)[0].strip()

    return {"title": title, "content": blog_content}


def normalize_venue_name(short_name: str) -> str:
    """
    엑셀의 축약 웨딩홀명을 네이버에서 쓰는 정식 명칭으로 변환

    예: "영등포jk" → "영등포JK아트컨벤션"
        "더채플" → "더채플앳청담"
    """
    VENUE_MAP = {
        "영등포jk": "영등포JK아트컨벤션",
        "jk아트": "영등포JK아트컨벤션",
        "더채플": "더채플앳청담",
        "더채플청담": "더채플앳청담",
        "아펠가모": "아펠가모 강남",
        "루이비스": "루이비스컨벤션",
        "그랜드힐": "그랜드힐 컨벤션",
        "빌라드지디": "빌라드지디",
        "소노펠리체": "소노펠리체컨벤션",
        "더컨벤션": "더컨벤션 서울",
        "노블발렌티": "노블발렌티 대치",
        "라온제나": "라온제나",
    }
    key = short_name.strip().lower().replace(" ", "")
    for k, v in VENUE_MAP.items():
        if k.lower().replace(" ", "") == key:
            return v
    return short_name


if __name__ == "__main__":
    venue = normalize_venue_name("영등포jk")
    print(f"웨딩홀 정식명: {venue}")
    print("=" * 60)

    result = generate_wedding_blog(venue_name=venue, num_photos=30)

    if result:
        print(f"\n[제목]\n{result['title']}")
        print(f"\n[본문]")
        sections = result["content"].split("[SECTION_BREAK]")
        for i, section in enumerate(sections, 1):
            print(f"\n--- 섹션 {i} ---")
            print(section.strip())
        print(f"\n총 {len(sections)}개 섹션")
    else:
        print("글 생성 실패")

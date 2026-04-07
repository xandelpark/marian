"""
웨딩 블로그 글 생성 모듈
- 웨딩홀 이름을 받아서 블로그 제목 + 본문을 생성
- [SECTION_BREAK]로 섹션 구분 (이미지 삽입 포인트)
"""
import subprocess
import json
import re


def generate_wedding_blog(
    venue_name: str,
    bride_name: str,
    shoot_date: str,
    num_photos: int = 30,
) -> dict:
    """
    웨딩 촬영 블로그 글을 생성합니다.

    Args:
        venue_name: 웨딩홀 이름 (예: "영등포JK아트컨벤션")
        bride_name: 신부 이름 (예: "아무개")
        shoot_date: 촬영 날짜 (예: "2025년 3월 1일")
        num_photos: 업로드할 사진 수 (섹션 수 결정에 사용)

    Returns:
        {"title": "...", "content": "...(SECTION_BREAK 포함)"}
    """
    # 사진 수에 따라 섹션 수 결정 (5~8장당 1섹션)
    num_sections = max(4, min(8, num_photos // 5))

    prompt = f"""당신은 '마리안웨딩'의 웨딩 촬영 전문 작가입니다.
아래 정보로 네이버 블로그 글을 작성해주세요.

[촬영 정보]
- 웨딩홀: {venue_name}
- 신부님: {bride_name} 신부님
- 촬영일: {shoot_date}

[작성 규칙]
1. 제목: "{venue_name} 본식스냅 - (감성적 부제)" 형식
2. 본문은 정확히 {num_sections}개 섹션으로 나누고, 각 섹션 사이에 [SECTION_BREAK]를 넣어주세요
3. 첫 섹션: 인사 + 웨딩홀 소개
4. 중간 섹션들: 촬영 순서대로 (준비, 리허설, 본식, 축하, 야외 등)
5. 마지막 섹션: 마무리 인사 + 마리안웨딩 문의 안내
6. 톤: 따뜻하고 감성적이지만 과하지 않게, 자연스러운 일상체
7. 각 섹션은 3~5문장
8. 마크다운 기호(*, #, `, ~, >) 사용 금지
9. 이모지 사용 금지
10. "마리안웨딩" 브랜드명은 첫 섹션과 마지막 섹션에만

[출력 형식]
첫 줄: 제목만
둘째 줄부터: 본문 (섹션 사이에 [SECTION_BREAK])

제목과 본문 사이에 빈 줄 하나를 넣어주세요."""

    try:
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/tmp",
        )
        if result.returncode != 0:
            print(f"Claude CLI 오류: {result.stderr}")
            return None

        output = result.stdout.strip()
    except FileNotFoundError:
        # claude CLI가 없으면 기본 템플릿 반환
        print("Claude CLI를 찾을 수 없습니다. 기본 템플릿을 생성합니다.")
        output = _fallback_template(venue_name, bride_name, shoot_date, num_sections)
    except subprocess.TimeoutExpired:
        print("Claude CLI 타임아웃. 기본 템플릿을 생성합니다.")
        output = _fallback_template(venue_name, bride_name, shoot_date, num_sections)

    # 제목과 본문 분리
    lines = output.split("\n", 2)
    if len(lines) >= 2:
        title = lines[0].strip()
        content = "\n".join(lines[1:]).strip()
    else:
        title = f"{venue_name} 본식스냅 - 마리안웨딩"
        content = output

    return {"title": title, "content": content}


def _fallback_template(venue_name, bride_name, shoot_date, num_sections):
    """Claude CLI 없을 때 기본 템플릿"""
    sections = [
        f"안녕하세요 마리안웨딩입니다. {shoot_date}, {venue_name}에서 {bride_name} 신부님의 아름다운 결혼식을 촬영했습니다. 오늘도 설레는 마음으로 촬영 이야기를 전해드립니다.",
        f"{venue_name}은 자연광이 아름답게 들어오는 공간으로, 촬영하기에 정말 좋은 곳입니다. 특히 대기실의 부드러운 조명이 신부님의 준비 과정을 더욱 아름답게 담아줍니다.",
        f"{bride_name} 신부님의 리허설 순간입니다. 아버지와 함께 입장하시는 모습이 너무 감동적이었습니다. 그 순간의 떨림과 설렘이 사진 속에 그대로 담겼습니다.",
        f"본식이 시작되었습니다. 주례 앞에서 서약을 나누는 두 분의 모습이 정말 아름다웠습니다. 하객분들의 축하 속에서 빛나는 순간이었습니다.",
        f"축하 세레모니와 함께 즐거운 시간이 이어졌습니다. 가족과 친구들의 진심 어린 축하가 식장을 가득 채웠습니다.",
        f"{bride_name} 신부님, 다시 한번 진심으로 축하드립니다. 두 분의 앞날에 행복만 가득하시길 바랍니다. 본식스냅 문의는 마리안웨딩으로 연락 주세요.",
    ]
    used = sections[:num_sections]
    title = f"{venue_name} 본식스냅 - 빛나는 순간을 담다"
    content = "\n[SECTION_BREAK]\n".join(used)
    return f"{title}\n\n{content}"


def normalize_venue_name(short_name: str) -> str:
    """
    엑셀의 축약 웨딩홀명을 네이버에서 쓰는 정식 명칭으로 변환

    예: "영등포jk" → "영등포JK아트컨벤션"
        "더채플" → "더채플앳청담"
    """
    # 자주 쓰는 웨딩홀 매핑 (필요시 추가)
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
    # 매핑에 없으면 원본 반환
    return short_name


if __name__ == "__main__":
    # 테스트: 영등포JK아트컨벤션으로 블로그 글 생성
    venue = normalize_venue_name("영등포jk")
    print(f"웨딩홀 정식명: {venue}")
    print("=" * 60)

    result = generate_wedding_blog(
        venue_name=venue,
        bride_name="아무개",
        shoot_date="2025년 3월 1일",
        num_photos=30,
    )

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

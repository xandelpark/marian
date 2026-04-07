"""
프로젝트 1 통합 테스트: 블로그 글 생성 → 네이버 발행
맥미니에서 실행하세요 (Playwright + 브라우저 필요)

사용법:
    # 1. 먼저 세션 저장 (최초 1회)
    python naver_blog_publisher.py 세션 웨딩

    # 2. 테스트 발행 (테스트용 사진 경로 수정 필요)
    python test_blog_publish.py

    # 3. 실제 폴더 지정 발행
    python test_blog_publish.py --folder /path/to/250301.아무개신부님
"""
import asyncio
import os
import sys
import glob
import re
from blog_content_generator import generate_wedding_blog, normalize_venue_name
from naver_blog_publisher import upload_to_naver_blog

# 설정
BLOG_ID = "marianwedding"
STATE_FILE = "naver_state.json"
MAX_PHOTOS = 30  # 최대 업로드 사진 수


def parse_folder_name(folder_name: str) -> dict:
    """
    폴더명에서 날짜와 이름 추출
    예: "250301.아무개신부님" → {"date": "2025년 3월 1일", "name": "아무개"}
        "250301.아무개" → {"date": "2025년 3월 1일", "name": "아무개"}
    """
    match = re.match(r"(\d{6})\.(.+)", folder_name)
    if not match:
        return None

    date_str = match.group(1)
    name_raw = match.group(2)

    # 날짜 파싱 (YYMMDD)
    yy, mm, dd = int(date_str[:2]), int(date_str[2:4]), int(date_str[4:6])
    year = 2000 + yy
    date_formatted = f"{year}년 {mm}월 {dd}일"

    # 이름에서 "신부님" 제거
    name = name_raw.replace("신부님", "").strip()

    return {"date": date_formatted, "name": name}


def get_photos_from_folder(folder_path: str, max_count: int = MAX_PHOTOS) -> list:
    """폴더에서 사진 파일 목록 가져오기 (JPG/JPEG/PNG)"""
    extensions = ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG", "*.png", "*.PNG"]
    photos = []
    for ext in extensions:
        photos.extend(glob.glob(os.path.join(folder_path, ext)))

    photos.sort()  # 파일명 순 정렬

    if len(photos) > max_count:
        # 균등 간격으로 선택
        step = len(photos) / max_count
        selected = [photos[int(i * step)] for i in range(max_count)]
        print(f"사진 {len(photos)}장 중 {max_count}장 선택")
        return selected

    print(f"사진 {len(photos)}장 발견")
    return photos


async def run_test(folder_path: str = None, venue_short: str = "영등포jk"):
    """테스트 실행"""
    # 1. 폴더 정보 파싱
    if folder_path:
        folder_name = os.path.basename(folder_path)
        info = parse_folder_name(folder_name)
        if not info:
            print(f"폴더명 형식 오류: {folder_name}")
            print("형식: YYMMDD.이름 (예: 250301.아무개신부님)")
            return
        photos = get_photos_from_folder(folder_path)
        if not photos:
            print(f"사진 없음: {folder_path}")
            return
    else:
        # 테스트 모드 - 사진 없이 글만 생성
        info = {"date": "2025년 3월 1일", "name": "아무개"}
        photos = []
        print("테스트 모드 (사진 없이 글만 생성)")

    # 2. 웨딩홀 이름 정규화
    venue = normalize_venue_name(venue_short)
    print(f"\n촬영일: {info['date']}")
    print(f"신부님: {info['name']}")
    print(f"웨딩홀: {venue_short} → {venue}")

    # 3. 블로그 글 생성
    print(f"\n블로그 글 생성 중...")
    result = generate_wedding_blog(
        venue_name=venue,
        bride_name=info["name"],
        shoot_date=info["date"],
        num_photos=len(photos) if photos else 30,
    )

    if not result:
        print("글 생성 실패!")
        return

    print(f"\n{'='*60}")
    print(f"[제목] {result['title']}")
    sections = result["content"].split("[SECTION_BREAK]")
    for i, s in enumerate(sections, 1):
        print(f"\n--- 섹션 {i} ---")
        print(s.strip()[:100] + "..." if len(s.strip()) > 100 else s.strip())
    print(f"\n총 {len(sections)}개 섹션, 사진 {len(photos)}장")
    print(f"{'='*60}")

    # 4. 발행 (사진이 있고 세션 파일이 있을 때만)
    if not photos:
        print("\n사진 없음 - 글 생성만 완료 (발행 생략)")
        return

    if not os.path.exists(STATE_FILE):
        print(f"\n세션 파일 없음: {STATE_FILE}")
        print("먼저 실행: python naver_blog_publisher.py 세션 웨딩")
        return

    confirm = input("\n발행하시겠습니까? (y/n): ").strip().lower()
    if confirm != "y":
        print("발행 취소")
        return

    success = await upload_to_naver_blog(
        title=result["title"],
        content=result["content"],
        image_paths=photos,
        state_file=STATE_FILE,
        blog_id=BLOG_ID,
    )

    if success:
        print("\n발행 성공!")
    else:
        print("\n발행 실패 - 로그를 확인하세요")


if __name__ == "__main__":
    folder = None
    venue = "영등포jk"

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--folder" and i < len(sys.argv) - 1:
            folder = sys.argv[i + 1]
        elif arg == "--venue" and i < len(sys.argv) - 1:
            venue = sys.argv[i + 1]

    asyncio.run(run_test(folder_path=folder, venue_short=venue))

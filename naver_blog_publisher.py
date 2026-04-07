"""
네이버 블로그 자동 발행 모듈 (jarvis_core.py에서 추출)
프로젝트 1: 웨딩 사진 블로그 자동 포스팅에 활용

의존성: playwright (pip install playwright && playwright install chromium)
사전 준비: 네이버 로그인 세션 파일 (naver_state.json) 필요
"""
import os, re, random, asyncio
from playwright.async_api import async_playwright


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 네이버 로그인 세션 저장 (최초 1회 실행 필요)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def save_naver_session(state_file: str, blog_id: str):
    """
    크롬 창을 열어 네이버 로그인 → 블로그 메인 이동 → 세션 저장

    사용법:
        asyncio.run(save_naver_session("naver_state.json", "marianwedding"))
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.goto("https://nid.naver.com/nidlogin.login")
        print(f"네이버 로그인 후 https://blog.naver.com/{blog_id} 까지 이동해주세요.")
        print("이동 완료되면 터미널에서 Enter를 눌러주세요...")
        await asyncio.get_event_loop().run_in_executor(None, input)
        await ctx.storage_state(path=state_file)
        await browser.close()
    print(f"세션 저장 완료: {state_file}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 네이버 블로그 발행 (핵심 함수)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def upload_to_naver_blog(
    title: str,
    content: str,
    image_paths: list,
    state_file: str,
    blog_id: str,
    video_path: str = None
) -> bool:
    """
    네이버 블로그에 글+이미지+동영상을 자동 발행

    Args:
        title: 블로그 제목
        content: 본문 텍스트 ([SECTION_BREAK]로 섹션 구분)
        image_paths: 이미지 파일 경로 리스트
        state_file: 네이버 로그인 세션 파일 경로
        blog_id: 네이버 블로그 ID
        video_path: (선택) 동영상 파일 경로

    Returns:
        True: 발행 성공, False: 발행 실패

    사용 예시:
        success = await upload_to_naver_blog(
            title="강남 더채플 본식스냅 - 촬영작가만 아는 빛의 비밀",
            content="안녕하세요 마리안웨딩입니다.[SECTION_BREAK]강남 더채플은...",
            image_paths=["/path/to/img1.jpg", "/path/to/img2.jpg"],
            state_file="naver_state.json",
            blog_id="marianwedding"
        )
    """
    print(f"\n[블로그 퍼블리싱] {blog_id} 작업 시작...")
    abs_image_paths = [os.path.abspath(p) for p in image_paths]

    # 마크다운 특수문자 제거
    for char in ["*", "#", "`", "~", ">"]:
        content = content.replace(char, "")

    # 섹션 분리 → 이미지 균등 배분
    raw_chunks = content.split("[SECTION_BREAK]")
    chunks = [chunk.strip() for chunk in raw_chunks if chunk.strip()]
    num_images = len(abs_image_paths)

    if num_images > 0 and chunks:
        if len(chunks) >= num_images:
            merged, per, remainder, idx = [], len(chunks) // num_images, len(chunks) % num_images, 0
            for i in range(num_images):
                take = per + (1 if i < remainder else 0)
                merged.append("\n\n".join(chunks[idx:idx+take]))
                idx += take
            chunks = merged
        else:
            all_sentences = []
            for chunk in chunks:
                parts = re.split(r"(?<=[.!?])\s+", chunk)
                for p in parts:
                    if len(p.strip()) > 8:
                        all_sentences.append(p.strip())
            if len(all_sentences) >= num_images:
                per, remainder, new_chunks, idx = len(all_sentences) // num_images, len(all_sentences) % num_images, [], 0
                for i in range(num_images):
                    take = per + (1 if i < remainder else 0)
                    new_chunks.append(" ".join(all_sentences[idx:idx+take]))
                    idx += take
                chunks = new_chunks
            else:
                while len(chunks) < num_images:
                    chunks.append(chunks[-1] if chunks else "")

    num_text_chunks = len(chunks)
    browser = None

    try:
        async with async_playwright() as p:
            # 브라우저 실행 (사람처럼 보이도록 slow_mo 적용)
            browser = await p.chromium.launch(headless=False, slow_mo=random.randint(150, 350))
            context_pw = await browser.new_context(
                storage_state=state_file,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context_pw.new_page()

            # 블로그 글쓰기 페이지 이동
            await page.goto(f"https://blog.naver.com/{blog_id}?Redirect=Write")
            await page.wait_for_load_state("networkidle")
            frame = page.frame_locator("iframe#mainFrame")
            await asyncio.sleep(random.uniform(4.0, 6.0))
            await page.keyboard.press("Escape")

            # 방해 요소 숨기기
            await frame.locator("body").evaluate("""() => {
                const style = document.createElement('style');
                style.innerHTML = `button[data-name="strike"], .se-popup-toolbar, .se-help-panel { display: none !important; }`;
                document.head.appendChild(style);
            }""")
            try:
                cancel_btn = frame.locator(".se-popup-button-cancel, .se-help-panel-close-button").first
                if await cancel_btn.is_visible(timeout=3000):
                    await cancel_btn.click()
            except:
                pass

            # === 제목 입력 ===
            title_area = frame.locator(".se-title-text").first
            await title_area.click(click_count=3, force=True)
            await asyncio.sleep(random.uniform(0.5, 1.2))
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.5)
            safe_title = title if title.strip() else "포스팅"
            for char in safe_title:
                await page.keyboard.type(char, delay=random.randint(50, 150))
            await asyncio.sleep(random.uniform(1.0, 2.5))

            # === 본문 영역 클릭 ===
            try:
                main_canvas = frame.locator(".se-main-container, .se-viewer, .se-content").first
                await main_canvas.click(position={"x": 50, "y": 50}, force=True)
            except:
                await page.mouse.click(500, 500)
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")

            # === 텍스트 + 이미지 교차 입력 ===
            max_loop = max(num_text_chunks, num_images)
            for i in range(max_loop):
                # 텍스트 입력
                if i < num_text_chunks and chunks[i]:
                    for char in chunks[i]:
                        await page.keyboard.type(char, delay=random.randint(20, 60))
                    await asyncio.sleep(random.uniform(1.0, 3.5))
                    await page.keyboard.press("Enter")
                    await page.keyboard.press("Enter")

                # 이미지 업로드
                if i < num_images:
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    async with page.expect_file_chooser(timeout=60000) as fc_info:
                        await frame.locator("button.se-document-toolbar-image-button, button[data-name='image']").first.click(force=True)
                    await (await fc_info.value).set_files(abs_image_paths[i])
                    await asyncio.sleep(random.uniform(8.0, 12.0))
                    await page.keyboard.press("ArrowRight")
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    await page.keyboard.press("Enter")
                    await page.keyboard.press("Enter")

            # === 동영상 업로드 (선택) ===
            if video_path and os.path.exists(video_path):
                try:
                    await page.keyboard.press("Enter")
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(2.0)
                    await frame.locator("button[data-name='video']").first.click(force=True)
                    await asyncio.sleep(2.5)
                    btn_selectors = [
                        "button.nvu_btn_append.nvu_local",
                        "button.nvu_btn_local",
                        "button[class*='nvu_btn_local']"
                    ]
                    video_uploaded = False
                    for sel in btn_selectors:
                        try:
                            async with page.expect_file_chooser(timeout=15000) as fc_info:
                                await frame.locator(sel).first.click(force=True)
                            await (await fc_info.value).set_files(os.path.abspath(video_path))
                            video_uploaded = True
                            break
                        except:
                            pass
                    if video_uploaded:
                        await asyncio.sleep(random.uniform(3.0, 5.0))
                        try:
                            title_input = frame.locator("#nvu_inp_box_title").first
                            if await title_input.is_visible(timeout=8000):
                                await title_input.click()
                                await title_input.fill(title)
                                await asyncio.sleep(0.8)
                        except:
                            pass
                        for method_js in [
                            "document.querySelector('button.nvu_btn_submit.nvu_btn_type2').click()",
                            "Array.from(document.querySelectorAll('button.nvu_btn_type2')).find(b=>b.innerText.trim()==='완료')?.click()"
                        ]:
                            try:
                                await frame.evaluate(method_js)
                                await asyncio.sleep(2.0)
                                break
                            except:
                                pass
                        await asyncio.sleep(random.uniform(20.0, 30.0))
                        await page.keyboard.press("ArrowRight")
                        await asyncio.sleep(1.0)
                except Exception as ve:
                    print(f"동영상 업로드 오류: {ve}")

            # === 사람처럼 스크롤 ===
            for _ in range(random.randint(2, 5)):
                await page.mouse.wheel(0, random.choice([-300, 300, 500, -500]))
                await asyncio.sleep(random.uniform(2.0, 5.0))
            await asyncio.sleep(random.randint(5, 35))

            # === 발행 버튼 클릭 ===
            await frame.locator("body").evaluate("""() => {
                const topBtn = document.querySelector('.se-publish-button')
                    || Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === '발행');
                if(topBtn) topBtn.click();
            }""")
            await asyncio.sleep(random.uniform(2.0, 4.0))

            # === 발행 확인 버튼 클릭 ===
            await frame.locator("body").evaluate("""() => {
                const confirmBtn = document.querySelector('.se-btn-publish, .confirm_btn')
                    || Array.from(document.querySelectorAll('button')).reverse().find(b => b.innerText.trim() === '발행');
                if(confirmBtn) confirmBtn.click();
            }""")
            await asyncio.sleep(15)

            return True

    except Exception as e:
        print(f"블로그 발행 오류: {e}")
        return False
    finally:
        if browser:
            await browser.close()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 블로그 계정 설정 (jarvis_core.py에서 추출)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOG_ACCOUNTS = {
    "웨딩": {"state_file": "naver_state.json", "blog_id": "marianwedding", "brand": "마리안웨딩"},
    "스냅": {"state_file": "naver_state_snap.json", "blog_id": "mariansnap", "brand": "마리안웨딩"},
    "오르비": {"state_file": "naver_state_orbi.json", "blog_id": "orbiart_", "brand": "오르비아트"},
    "티": {"state_file": "naver_state_review.json", "blog_id": "xandel1397", "brand": "T명적소비"},
    "아트": {"state_file": "naver_state_art.json", "blog_id": "artcollective", "brand": "마리안웨딩"},
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 블로그 트리거 목록 (jarvis_core.py에서 추출)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOG_TRIGGERS = {
    "블로그 웨딩":   {"brand": "마리안웨딩",    "state_file": "naver_state.json",        "blog_id": "marianwedding"},
    "블로그 스냅":   {"brand": "마리안웨딩",    "state_file": "naver_state_snap.json",    "blog_id": "mariansnap"},
    "블로그 오르비": {"brand": "오르비아트",    "state_file": "naver_state_orbi.json",    "blog_id": "orbiart_"},
    "블로그 티":     {"brand": "T명적소비",     "state_file": "naver_state_review.json",  "blog_id": "xandel1397"},
    "블로그 아트":   {"brand": "마리안웨딩",    "state_file": "naver_state_art.json",     "blog_id": "artcollective"},
    "블로그 맛집":   {"brand": "T명적소비맛집", "state_file": "naver_state_review.json",  "blog_id": "xandel1397"},
    "블로그 여행":   {"brand": "T명적소비여행", "state_file": "naver_state_review.json",  "blog_id": "xandel1397"},
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 단독 실행 테스트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "세션":
        # 세션 저장 모드: python naver_blog_publisher.py 세션 웨딩
        key = sys.argv[2] if len(sys.argv) > 2 else "웨딩"
        acc = BLOG_ACCOUNTS.get(key)
        if acc:
            asyncio.run(save_naver_session(acc["state_file"], acc["blog_id"]))
        else:
            print(f"알 수 없는 키: {key}. 사용 가능: {list(BLOG_ACCOUNTS.keys())}")
    else:
        print("네이버 블로그 자동 발행 모듈")
        print("=" * 50)
        print("\n[세션 저장]")
        print("  python naver_blog_publisher.py 세션 웨딩")
        print("  python naver_blog_publisher.py 세션 오르비")
        print("\n[코드에서 사용]")
        print("  from naver_blog_publisher import upload_to_naver_blog")
        print("  success = await upload_to_naver_blog(title, content, images, state_file, blog_id)")
        print("\n[블로그 트리거 (텔레그램)]")
        for trigger in BLOG_TRIGGERS:
            print(f"  {trigger} [키워드]")

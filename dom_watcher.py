import json
import random
import time
import winsound
from pathlib import Path

import win32con
import win32gui
from playwright.sync_api import Page, sync_playwright
from plyer import notification

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "dom_config.json"
CDP_URL = "http://localhost:9222"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def find_korail_page(browser) -> Page:
    for context in browser.contexts:
        for page in context.pages:
            if "korail.com/ticket/search" in page.url:
                return page
    raise RuntimeError(
        "korail.com 승차권 조회 결과 탭을 찾을 수 없습니다. "
        "디버그 모드 크롬에서 원하는 구간/날짜로 조회한 뒤 다시 실행하세요."
    )


def _human_pause():
    """로딩이 끝난 걸 인지하고 다음 동작을 하기까지, 사람이라면 있었을 법한
    짧은 반응 시간을 흉내낸다(매번 똑같은 간격이면 오히려 기계적으로 보임)."""
    time.sleep(random.uniform(0.15, 0.5))


def _wait_row_count_change(page: Page, before: int, timeout_ms: int = 2500):
    """li.tckList 개수가 바뀔 때까지(=AJAX 렌더링이 끝날 때까지) 기다린다.
    고정 sleep 대신 실제로 끝나는 시점에 바로 다음 동작으로 넘어가기 위함."""
    try:
        page.wait_for_function(
            "(before) => document.querySelectorAll('li.tckList').length !== before",
            arg=before,
            timeout=timeout_ms,
        )
    except Exception:
        pass  # 타임아웃이면 그냥 지금 상태로 진행(다음 사이클에서 다시 시도됨)


def _wait_list_reloaded(page: Page, timeout_ms: int = 3000):
    """날짜 이동 버튼을 누르면 목록이 한 번 비었다가(0개) 다시 채워진다.
    #startDate 값은 실제 목록보다 먼저 바뀌어서 신호로 쓰면 너무 일찍
    다음 동작으로 넘어가 버리므로(실측으로 확인됨), 대신 "먼저 비워지고
    다시 채워지는" 실제 DOM 상태 변화를 직접 감지한다."""
    try:
        # 비워지는 순간을 잡을 수 있으면 잡는다(놓쳐도 무방 - 아래서 어차피 채워짐만 확인).
        page.wait_for_function(
            "() => document.querySelectorAll('li.tckList').length === 0",
            timeout=400,
        )
    except Exception:
        pass
    try:
        page.wait_for_function(
            "() => document.querySelectorAll('li.tckList').length > 0",
            timeout=timeout_ms,
        )
    except Exception:
        pass


def refresh(page: Page):
    """다음날 -> 이전날 버튼을 눌러 같은 날짜 목록을 새로고침한다. 페이지
    전체를 새로고침(F5)하면 코레일 대기실(넷퍼넬) 화면이 다시 뜰 수 있어서,
    AJAX로 날짜만 바꾸는 이 버튼들을 대신 사용한다."""
    page.click("#dateinput__next")
    _wait_list_reloaded(page)
    _human_pause()
    page.click("#dateinput__prev")
    _wait_list_reloaded(page)
    _human_pause()


def expand_all(page: Page, max_clicks: int):
    """열차 목록은 새로고침할 때마다 처음 10개만 보이므로, "더보기" 버튼이
    더 이상 없을 때까지(=그날 목록을 전부 불러올 때까지) 반복 클릭한다."""
    for _ in range(max_clicks):
        more = page.query_selector("a.page_group")
        if more is None or not more.is_visible():
            break
        before = page.locator("li.tckList").count()
        more.click()
        _wait_row_count_change(page, before, timeout_ms=2000)
        _human_pause()


def read_rows(page: Page) -> list[dict]:
    """열차 행(li.tckList)마다 열차번호/출발시각과, 좌석등급별 매진 여부를
    DOM에서 직접 읽는다. 좌석등급 중 하나라도 "매진이 아니고 실제로 판매하는
    등급"이면(=자리가 있으면) sold_out=False 로 판단한다. 텍스트가 "-"인
    칸은 그 열차에 해당 등급 자체가 없다는 뜻이라 "좌석 있음"으로 치지
    않는다(예: ITX-새마을/무궁화는 특실 칸이 항상 "-")."""
    return page.eval_on_selector_all(
        "li.tckList",
        r"""
        (rows) => rows.map(li => {
            const text = li.textContent;
            const timeMatch = text.match(/\((\d{2}:\d{2})\s*~\s*\d{2}:\d{2}\)/);
            const numMatch = text.match(/(?:KTX-산천|KTX|ITX-청춘|새마을호|무궁화호|SRT)\s*(\d{3})/);
            const boxes = [...li.querySelectorAll('.price_box')].map(b => ({
                soldOut: b.classList.contains('sold_out'),
                na: b.textContent.trim() === '-',
            }));
            const hasAvailable = boxes.some(b => !b.soldOut && !b.na);
            return {
                no: numMatch ? numMatch[1] : null,
                dep: timeMatch ? timeMatch[1] : null,
                soldOut: boxes.length > 0 && !hasAvailable,
            };
        })
        """,
    )


def bring_chrome_to_front():
    candidates = []

    def _enum(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            if "Chrome" in title and (rect[2] - rect[0]) > 500:
                candidates.append((hwnd, rect[2] - rect[0]))

    win32gui.EnumWindows(_enum, None)
    if not candidates:
        return
    candidates.sort(key=lambda c: -c[1])
    hwnd = candidates[0][0]
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass


def alert(target_name: str):
    for _ in range(5):
        winsound.Beep(1000, 400)
        time.sleep(0.2)
    notification.notify(
        title="KTX 좌석 알림",
        message=f"[{target_name}] 좌석이 생겼습니다! 코레일 사이트에서 직접 예매하세요.",
        timeout=15,
    )
    bring_chrome_to_front()


def main():
    config = load_config()
    interval_min = config.get("check_interval_sec_min", config.get("check_interval_sec", 5))
    interval_max = config.get("check_interval_sec_max", interval_min)
    targets = config["targets"]
    already_alerted = set()
    pending_confirm = set()  # 직전 사이클에 "좌석 발견"으로 나왔던 열차들

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            raise RuntimeError(
                "크롬 디버그 포트(9222)에 연결할 수 없습니다. "
                "크롬을 --remote-debugging-port=9222 옵션으로 다시 실행했는지 확인하세요."
            ) from e
        page = find_korail_page(browser)

        print(f"좌석 모니터링을 시작합니다 ({len(targets)}개 열차). Ctrl+C 로 종료하세요.")
        print(f"※ 대상 탭: {page.url}")

        try:
            while True:
                refresh(page)
                expand_all(page, config.get("more_button_max_clicks", 6))
                rows = read_rows(page)
                by_key = {
                    (r["no"], r["dep"]): r["soldOut"]
                    for r in rows
                    if r["no"] and r["dep"]
                }

                still_pending = set()
                for t in targets:
                    name = t["name"]
                    if name in already_alerted:
                        continue
                    sold_out = by_key.get((t["no"], t["dep"]))
                    ts = time.strftime("%H:%M:%S")
                    if sold_out is None:
                        print(f"[{ts}] {name}: 목록에서 못 찾음(날짜/구간을 확인하세요)")
                        continue
                    if not sold_out:
                        if name in pending_confirm:
                            # DOM 값도 렌더링 타이밍에 따라 간헐적으로 흔들릴 수 있으므로,
                            # 2번 연속 "좌석 발견"이 나와야만 진짜로 알림을 보낸다.
                            print(f"[{ts}] {name}: 좌석 발견 재확인! 알림을 보냅니다.")
                            already_alerted.add(name)
                            alert(name)
                        else:
                            print(f"[{ts}] {name}: 좌석 발견(재확인 대기 중)...")
                            still_pending.add(name)
                    else:
                        print(f"[{ts}] {name}: 매진 상태 유지 중...")
                pending_confirm = still_pending

                if len(already_alerted) == len(targets):
                    print("모든 대상 열차에 좌석이 확인되었습니다. 종료합니다.")
                    break

                if interval_max > 0:
                    time.sleep(random.uniform(interval_min, interval_max))
        except KeyboardInterrupt:
            print("\n모니터링을 종료합니다.")


if __name__ == "__main__":
    main()

import ctypes

import dpi_awareness  # noqa: F401  (pyautogui/pygetwindow보다 먼저 import 해야 함)

import json
import time
import winsound
from ctypes import wintypes
from pathlib import Path

import pyautogui
import pygetwindow as gw
import pyscreeze
from PIL import ImageGrab
from plyer import notification

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def find_chrome_window():
    for win in gw.getWindowsWithTitle(""):
        title = (win.title or "").lower()
        if "chrome" in title or "코레일" in title or "korail" in title:
            return win
    return None


def get_monitor_rects():
    """감지된 모니터들의 (left, top, right, bottom)을 순서대로 반환합니다.
    순서는 list_monitors.py 로 미리 확인하세요."""
    rects = []
    MonitorEnumProc = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(wintypes.RECT),
        ctypes.c_double,
    )

    def _callback(hmonitor, hdc, rect_ptr, data):
        r = rect_ptr.contents
        rects.append((r.left, r.top, r.right, r.bottom))
        return 1

    ctypes.windll.user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(_callback), 0)
    return rects


def move_window_to_monitor(win, monitor_number: int):
    """monitor_number 는 1부터 시작 (list_monitors.py 의 [감지 순번] 기준)."""
    rects = get_monitor_rects()
    index = monitor_number - 1
    if not (0 <= index < len(rects)):
        print(f"경고: {monitor_number}번 모니터를 찾을 수 없습니다 (감지된 모니터 {len(rects)}개).")
        return
    left, top, _, _ = rects[index]
    try:
        win.moveTo(left + 50, top + 50)
    except Exception:
        pass


def alert(config: dict, target_name: str, move_to_alert_monitor: bool):
    """move_to_alert_monitor 는 이 알림 이후 더 이상 화면 좌표 기반 감시가 필요 없을
    때(=이번이 마지막 대상)만 True 로 넘겨야 합니다. 서로 배율(DPI)이 다른 모니터
    사이를 오가면 창 위치가 픽셀 단위로 정확히 복원되지 않아, 감시 중 창을 옮기면
    남은 열차의 좌표 기반 캡처/클릭이 어긋날 수 있기 때문입니다."""
    for _ in range(5):
        winsound.Beep(1000, 400)
        time.sleep(0.2)
    notification.notify(
        title="KTX 좌석 알림",
        message=f"[{target_name}] 좌석이 생겼습니다! 코레일 사이트에서 직접 예매하세요.",
        timeout=15,
    )
    win = find_chrome_window()
    if win is None:
        return
    try:
        if win.isMinimized:
            win.restore()
        alert_monitor = config.get("alert_monitor")
        if move_to_alert_monitor and alert_monitor is not None:
            move_window_to_monitor(win, alert_monitor)
        win.activate()
    except Exception:
        pass


def refresh_results(config: dict):
    r = config["refresh"]
    pyautogui.click(r["next_day_button"]["x"], r["next_day_button"]["y"])
    time.sleep(1.5)
    pyautogui.click(r["prev_day_button"]["x"], r["prev_day_button"]["y"])
    time.sleep(1.5)
    # 새로고침을 반복하다 보면 페이지 스크롤이 조금씩 밀리는 경우가 있어, 좌표 기준이
    # 어긋나지 않도록 매 사이클마다 스크롤을 맨 위로 강제 초기화한다.
    scroll_x = r["next_day_button"]["x"]
    scroll_y = r["next_day_button"]["y"] + 200
    pyautogui.scroll(600, x=scroll_x, y=scroll_y)
    time.sleep(0.3)


def is_sold_out(config: dict, target: dict) -> bool:
    """pyautogui.locateOnScreen()은 기본적으로 주 모니터만 캡처하므로, 코레일 창이
    다른 모니터에 있으면 항상 못 찾는다. 모든 모니터를 포함해 직접 캡처한다."""
    left, top, width, height = (
        target["left"],
        target["top"],
        target["width"],
        target["height"],
    )
    template_path = BASE_DIR / config["sold_out_template"]
    confidence = config.get("match_confidence", 0.85)

    screenshot = ImageGrab.grab(all_screens=True)
    region_im = screenshot.crop((left, top, left + width, top + height))
    try:
        match = pyscreeze.locate(str(template_path), region_im, confidence=confidence)
    except pyscreeze.ImageNotFoundException:
        match = None
    return match is not None


def main():
    config = load_config()
    interval = config.get("check_interval_sec", 20)
    targets = config["targets"]
    already_alerted = set()

    print(f"좌석 모니터링을 시작합니다 ({len(targets)}개 열차). Ctrl+C 로 종료하세요.")
    print("※ 브라우저 창을 이동/최소화/가리지 마세요 (화면 좌표 기반으로 동작합니다).")
    if config.get("alert_monitor") is not None:
        print(f"※ 마지막 열차 알림 시 크롬 창을 {config['alert_monitor']}번 모니터로 이동합니다.")

    try:
        while True:
            refresh_results(config)

            pending = [t for t in targets if t["name"] not in already_alerted]
            found = [t for t in pending if not is_sold_out(config, t)]

            # 남은 열차가 한 사이클에 전부 동시에 "발견"되면 실제 좌석 오픈이 아니라
            # 코레일 사이트의 대기실 팝업 등으로 화면을 통째로 못 읽은 오탐일 가능성이
            # 매우 높다. 이 경우 알림 없이 건너뛰고 다음 사이클에 다시 확인한다.
            if pending and len(found) == len(pending) and len(pending) > 1:
                print(
                    f"[{time.strftime('%H:%M:%S')}] 남은 열차 {len(pending)}개가 "
                    "한꺼번에 매진 해제로 감지되어 오탐으로 보고 이번 사이클은 건너뜁니다."
                )
                time.sleep(interval)
                continue

            for target in pending:
                name = target["name"]
                if target in found:
                    print(f"[{time.strftime('%H:%M:%S')}] {name}: 좌석 발견! 알림을 보냅니다.")
                    already_alerted.add(name)
                    is_last = len(already_alerted) == len(targets)
                    alert(config, name, move_to_alert_monitor=is_last)
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] {name}: 매진 상태 유지 중...")

            if len(already_alerted) == len(targets):
                print("모든 대상 열차에 좌석이 확인되었습니다. 종료합니다.")
                break

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n모니터링을 종료합니다.")


if __name__ == "__main__":
    main()

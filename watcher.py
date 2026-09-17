import json
import time
import winsound
from pathlib import Path

import pyautogui
import pygetwindow as gw
from plyer import notification

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def bring_chrome_to_front():
    for win in gw.getWindowsWithTitle(""):
        title = (win.title or "").lower()
        if "chrome" in title or "코레일" in title or "korail" in title:
            try:
                if win.isMinimized:
                    win.restore()
                win.activate()
            except Exception:
                pass
            return


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


def refresh_results(config: dict):
    r = config["refresh"]
    pyautogui.click(r["next_day_button"]["x"], r["next_day_button"]["y"])
    time.sleep(1.5)
    pyautogui.click(r["prev_day_button"]["x"], r["prev_day_button"]["y"])
    time.sleep(1.5)


def is_sold_out(config: dict, target: dict) -> bool:
    region = (target["left"], target["top"], target["width"], target["height"])
    template_path = BASE_DIR / config["sold_out_template"]
    confidence = config.get("match_confidence", 0.85)

    match = pyautogui.locateOnScreen(
        str(template_path), region=region, confidence=confidence
    )
    return match is not None


def main():
    config = load_config()
    interval = config.get("check_interval_sec", 20)
    targets = config["targets"]
    already_alerted = set()

    print(f"좌석 모니터링을 시작합니다 ({len(targets)}개 열차). Ctrl+C 로 종료하세요.")
    print("※ 브라우저 창을 이동/최소화/가리지 마세요 (화면 좌표 기반으로 동작합니다).")

    try:
        while True:
            refresh_results(config)

            for target in targets:
                name = target["name"]
                if name in already_alerted:
                    continue

                if is_sold_out(config, target):
                    print(f"[{time.strftime('%H:%M:%S')}] {name}: 매진 상태 유지 중...")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] {name}: 좌석 발견! 알림을 보냅니다.")
                    alert(name)
                    already_alerted.add(name)

            if len(already_alerted) == len(targets):
                print("모든 대상 열차에 좌석이 확인되었습니다. 종료합니다.")
                break

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n모니터링을 종료합니다.")


if __name__ == "__main__":
    main()

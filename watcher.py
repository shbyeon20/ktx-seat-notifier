import json
import time
import winsound
from pathlib import Path

import pyautogui
from plyer import notification

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def alert():
    for _ in range(5):
        winsound.Beep(1000, 400)
        time.sleep(0.2)
    notification.notify(
        title="KTX 좌석 알림",
        message="지정한 열차에 좌석이 생겼습니다! 코레일 사이트에서 직접 예매하세요.",
        timeout=15,
    )


def is_sold_out(config: dict) -> bool:
    r = config["seat_status_region"]
    region = (r["left"], r["top"], r["width"], r["height"])
    template_path = BASE_DIR / config["sold_out_template"]
    confidence = config.get("match_confidence", 0.85)

    match = pyautogui.locateOnScreen(
        str(template_path), region=region, confidence=confidence
    )
    return match is not None


def main():
    config = load_config()
    button = config["search_button"]
    interval = config.get("check_interval_sec", 20)

    print("좌석 모니터링을 시작합니다. Ctrl+C 로 종료하세요.")
    print("※ 브라우저 창을 이동/최소화/가리지 마세요 (화면 좌표 기반으로 동작합니다).")

    try:
        while True:
            pyautogui.click(button["x"], button["y"])
            time.sleep(3)  # 검색 결과 갱신 대기

            if is_sold_out(config):
                print(f"[{time.strftime('%H:%M:%S')}] 매진 상태 유지 중...")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] 좌석 발견! 알림을 보냅니다.")
                alert()

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n모니터링을 종료합니다.")


if __name__ == "__main__":
    main()

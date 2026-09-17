import json
import time
from pathlib import Path

import pyautogui

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
TEMPLATES_DIR = BASE_DIR / "templates"


def wait_for_point(label: str) -> tuple[int, int]:
    print(f"\n{label} 위치에 마우스를 올리고 3초간 기다리세요...")
    time.sleep(3)
    x, y = pyautogui.position()
    print(f"  -> {label}: x={x}, y={y}")
    return x, y


def main():
    TEMPLATES_DIR.mkdir(exist_ok=True)

    print("=== 좌석 상태(예: '매진' 글자)가 표시되는 영역을 지정합니다 ===")
    left, top = wait_for_point("영역의 좌측 상단")
    right, bottom = wait_for_point("영역의 우측 하단")

    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        raise ValueError("좌측 상단이 우측 하단보다 오른쪽/아래에 있습니다. 다시 시도하세요.")

    region = (left, top, width, height)
    print(f"\n지정된 영역: {region}")

    input("\n해당 열차가 지금 '매진' 상태인지 확인한 뒤 Enter 를 누르세요 (템플릿 캡처)...")
    screenshot = pyautogui.screenshot(region=region)
    template_path = TEMPLATES_DIR / "sold_out.png"
    screenshot.save(template_path)
    print(f"템플릿 저장 완료: {template_path}")

    config = {}
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    config["seat_status_region"] = {
        "left": left,
        "top": top,
        "width": width,
        "height": height,
    }
    config.setdefault("sold_out_template", "templates/sold_out.png")
    config.setdefault("check_interval_sec", 20)
    config.setdefault("match_confidence", 0.85)
    config.setdefault("search_button", {"x": 0, "y": 0})

    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"config.json 업데이트 완료: {CONFIG_PATH}")


if __name__ == "__main__":
    main()

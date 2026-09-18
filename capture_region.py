import dpi_awareness  # noqa: F401  (pyautogui보다 먼저 import 해야 함)

import json
import time
from pathlib import Path

import pyautogui
from PIL import ImageGrab

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
TEMPLATES_DIR = BASE_DIR / "templates"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_config(config: dict):
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def wait_for_point(label: str) -> tuple[int, int]:
    print(f"\n{label} 위치에 마우스를 올리고 3초간 기다리세요...")
    time.sleep(3)
    x, y = pyautogui.position()
    print(f"  -> {label}: x={x}, y={y}")
    return x, y


def capture_region(label: str) -> tuple[int, int, int, int]:
    left, top = wait_for_point(f"[{label}] 영역의 좌측 상단")
    right, bottom = wait_for_point(f"[{label}] 영역의 우측 하단")
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        raise ValueError("좌측 상단이 우측 하단보다 오른쪽/아래에 있습니다. 다시 시도하세요.")
    return left, top, width, height


def setup_refresh_buttons(config: dict):
    print("\n=== 새로고침용 버튼 좌표를 지정합니다 (예: 코레일 결과 화면의 '다음날'/'이전날' 화살표) ===")
    nx, ny = wait_for_point("'다음날' 화살표 버튼")
    px, py = wait_for_point("'이전날' 화살표 버튼")
    config["refresh"] = {
        "next_day_button": {"x": nx, "y": ny},
        "prev_day_button": {"x": px, "y": py},
    }


def add_target(config: dict, capture_template: bool):
    name = input("\n이 열차를 구분할 이름을 입력하세요 (예: KTX207 09:04): ").strip()
    left, top, width, height = capture_region(name)
    target = {"name": name or f"target_{len(config.get('targets', [])) + 1}",
              "left": left, "top": top, "width": width, "height": height}

    config.setdefault("targets", [])
    config["targets"] = [t for t in config["targets"] if t.get("name") != target["name"]]
    config["targets"].append(target)

    if capture_template:
        TEMPLATES_DIR.mkdir(exist_ok=True)
        input(f"\n'{name}' 열차가 지금 '매진' 상태인지 확인한 뒤 Enter 를 누르세요 (템플릿 캡처)...")
        # pyautogui.screenshot()은 주 모니터만 캡처하므로, 다른 모니터에 창이 있어도
        # 되도록 모든 모니터를 포함해 직접 캡처한다.
        screenshot = ImageGrab.grab(all_screens=True).crop(
            (left, top, left + width, top + height)
        )
        template_path = TEMPLATES_DIR / "sold_out.png"
        screenshot.save(template_path)
        print(f"템플릿 저장 완료: {template_path}")


def main():
    config = load_config()

    if input("\n새로고침 버튼 좌표를 (다시) 설정할까요? (y/N): ").strip().lower() == "y":
        setup_refresh_buttons(config)

    config.setdefault("sold_out_template", "templates/sold_out.png")
    config.setdefault("check_interval_sec", 20)
    config.setdefault("match_confidence", 0.85)
    config.setdefault("targets", [])

    template_exists = (BASE_DIR / config["sold_out_template"]).exists()

    while True:
        add_target(config, capture_template=not template_exists)
        template_exists = True
        save_config(config)
        if input("\n다른 열차도 추가할까요? (y/N): ").strip().lower() != "y":
            break

    print(f"\nconfig.json 업데이트 완료: {CONFIG_PATH}")


if __name__ == "__main__":
    main()

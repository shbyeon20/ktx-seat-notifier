import time

import pyautogui

print("마우스를 원하는 위치(예: '조회하기' 버튼)에 올려두세요.")
print("Ctrl+C 로 종료하면 마지막 좌표가 출력됩니다.\n")

try:
    while True:
        x, y = pyautogui.position()
        print(f"\r현재 좌표: x={x}, y={y}   ", end="", flush=True)
        time.sleep(0.2)
except KeyboardInterrupt:
    x, y = pyautogui.position()
    print(f"\n\n마지막 좌표: x={x}, y={y}")
    print("이 값을 config.json 의 search_button 에 입력하세요.")

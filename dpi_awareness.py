"""여러 모니터의 배율(DPI)이 서로 다르면, DPI를 인식하지 못하는 프로세스는 각
모니터의 좌표/픽셀을 가상 스케일로 뒤섞어 보고합니다. capture_region.py /
calibrate_position.py 로 잡은 좌표와 watcher.py가 실제로 클릭·캡처하는 좌표가
같은 기준을 쓰도록, 좌표를 다루는 모든 스크립트는 이 모듈을 **다른 import보다
먼저** import 해서 프로세스를 Per-Monitor DPI Aware로 맞춰야 합니다.

    import dpi_awareness  # 반드시 pyautogui/pygetwindow 등 보다 먼저

SetProcessDpiAwarenessContext 는 포인터 크기 인자를 받으므로 argtypes를 명시하지
않으면 64비트 파이썬에서 값이 잘못 전달되어 조용히 실패한다.
"""
import ctypes

DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)


def enable():
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        ctypes.windll.user32.SetProcessDpiAwarenessContext.restype = ctypes.c_int
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        ):
            return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        pass


enable()

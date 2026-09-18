"""config.json 의 alert_monitor 값을 정하기 위해, 이 컴퓨터에서 감지되는 모니터
순서와 위치를 출력합니다. Windows 디스플레이 설정의 "1, 2, 3" 배치와 비교해서
알림이 뜰 때 창을 옮길 모니터 번호를 확인하세요.
"""
import ctypes
from ctypes import wintypes

import dpi_awareness  # noqa: F401


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


MONITORINFOF_PRIMARY = 0x1


def list_monitors():
    results = []
    MonitorEnumProc = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(wintypes.RECT),
        ctypes.c_double,
    )

    def _callback(hmonitor, hdc, rect_ptr, data):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info))
        r = info.rcMonitor
        results.append(
            {
                "rect": (r.left, r.top, r.right, r.bottom),
                "primary": bool(info.dwFlags & MONITORINFOF_PRIMARY),
                "device": info.szDevice,
            }
        )
        return 1

    ctypes.windll.user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(_callback), 0)
    return results


def main():
    monitors = list_monitors()
    print(f"감지된 모니터 수: {len(monitors)}\n")
    for i, m in enumerate(monitors, start=1):
        left, top, right, bottom = m["rect"]
        primary = " (주 모니터)" if m["primary"] else ""
        print(
            f"[감지 순번 {i}]{primary} device={m['device']} "
            f"위치=({left}, {top}) 크기={right - left}x{bottom - top}"
        )
    print(
        "\nWindows 설정 > 디스플레이 화면에서 보이는 번호와 위 목록의 위치(x, y)를 "
        "비교해서, 알림이 뜰 때 창을 옮기고 싶은 모니터의 [감지 순번]을 "
        "config.json 의 \"alert_monitor\" 값으로 넣으세요."
    )


if __name__ == "__main__":
    main()

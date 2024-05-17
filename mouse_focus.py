import time
import win32gui
import win32process
import win32api
import psutil


# 获取当前前台窗口的进程ID
def get_foreground_window_process_id():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    return pid, hwnd


# 获取当前鼠标位置
def get_cursor_pos():
    return win32api.GetCursorPos()


# 判断鼠标是否在指定窗口内
def is_mouse_in_window(hwnd):
    rect = win32gui.GetWindowRect(hwnd)
    cursor_pos = get_cursor_pos()
    return rect[0] <= cursor_pos[0] <= rect[2] and rect[1] <= cursor_pos[1] <= rect[3]


# 判断鼠标是否在目标进程的窗口内
def is_mouse_focus_on(target_pid):
    pid, hwnd = get_foreground_window_process_id()
    if pid == target_pid:
        return is_mouse_in_window(hwnd)
    return False


# 通过进程名称获取进程ID
def get_pid_by_name(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return proc.info['pid']
    return None



if __name__ == "__main__":
    process_name = "NarakaBladepoint.exe"
    target_pid = get_pid_by_name(process_name)

    while True:
        result = is_mouse_focus_on(target_pid)
        print(result)
        time.sleep(1)

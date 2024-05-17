import time, threading
import win32api, win32con
import mouse_focus

process_name = "NarakaBladepoint.exe"
target_pid = mouse_focus.get_pid_by_name(process_name)


def new_thread(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
    return wrapper


def on_mouse_focus(func):
    def wrapper(*args, **kwargs):
        if mouse_focus.is_mouse_focus_on(target_pid):
            return func(*args, **kwargs)
    return wrapper


@new_thread
@on_mouse_focus
def keypress(key, delay0, delay1, delay2):
    # key实际上应为VK_CODE，这里我用不到，就简化为ascii了。
    # https://learn.microsoft.com/zh-cn/windows/win32/inputdev/virtual-key-codes
    time.sleep(delay0)
    win32api.keybd_event(ord(key), win32api.MapVirtualKey(ord(key), 0), 0, 0)
    time.sleep(delay1)
    win32api.keybd_event(ord(key), win32api.MapVirtualKey(ord(key), 0), win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(delay2)
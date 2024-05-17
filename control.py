import time
import win32api, win32con


def keypress(key, delay=0.01):
    # key实际上应为VK_CODE，这里我用不到，就简化为ascii了。
    # https://learn.microsoft.com/zh-cn/windows/win32/inputdev/virtual-key-codes
    win32api.keybd_event(ord(key), win32api.MapVirtualKey(ord(key), 0), 0, 0)
    time.sleep(delay)
    win32api.keybd_event(ord(key), win32api.MapVirtualKey(ord(key), 0), win32con.KEYEVENTF_KEYUP, 0)
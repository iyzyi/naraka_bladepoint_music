import asyncio
import win32api, win32con
import mouse_focus


process_name = "NarakaBladepoint.exe"
target_pid = mouse_focus.get_pid_by_name(process_name)


def on_mouse_focus(func):
    async def wrapper(*args, **kwargs):
        if mouse_focus.is_mouse_focus_on(target_pid):
            return func(*args, **kwargs)
    return wrapper


async def delay(seconds):
    await asyncio.sleep(seconds)


@on_mouse_focus
async def keypress(key, delay_seconds=0.01):
    # key实际上应为VK_CODE，这里我暂时用不到，就简化为ascii了。
    # https://learn.microsoft.com/zh-cn/windows/win32/inputdev/virtual-key-codes
    win32api.keybd_event(ord(key), win32api.MapVirtualKey(ord(key), 0), 0, 0)
    await delay(delay_seconds)
    win32api.keybd_event(ord(key), win32api.MapVirtualKey(ord(key), 0), win32con.KEYEVENTF_KEYUP, 0)


@on_mouse_focus
async def moveto(x, y):
    win32api.SetCursorPos((x, y))


@on_mouse_focus
async def left_click(delay_seconds=0.01):
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    await delay(delay_seconds)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


@on_mouse_focus
async def mouse_wheel(pixel):
    """
        滚动鼠标滚轮
        Args:
            pixel: 滚动像素量。正数表示向上滚动，负数表示向下滚动。
    """
    win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, pixel, 0)


if __name__ == '__main__':
    asyncio.run(delay(1))
    print('done')
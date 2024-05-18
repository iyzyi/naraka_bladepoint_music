import time
import win32api, win32con, win32gui
import mouse_focus


class OperationInterrupt(Exception):
    pass


def wrap_interrupt(func):
    def wrapper(self, *args, **kwargs):
        if self.is_interrupted:
            raise OperationInterrupt("stop control due to operation interrupt")
        else:
            return func(self, *args, **kwargs)
    return wrapper


def on_mouse_focus(func):
    @wrap_interrupt
    def wrapper(self, *args, **kwargs):
        if mouse_focus.is_mouse_focus_on(self.target_pid):
            return func(self, *args, **kwargs)
    return wrapper


class Control:
    def __init__(self, process_name):
        self.target_pid = mouse_focus.get_pid_by_name(process_name)
        self.is_interrupted = False

    def interrupt(self):
        self.is_interrupted = True

    @wrap_interrupt
    def delay(self, seconds):
        time.sleep(seconds)

    @on_mouse_focus
    def keypress(self, key, delay_seconds=0.01):
        # key实际上应为VK_CODE，这里我暂时用不到，就简化为ascii了。
        # https://learn.microsoft.com/zh-cn/windows/win32/inputdev/virtual-key-codes
        win32api.keybd_event(ord(key), win32api.MapVirtualKey(ord(key), 0), 0, 0)
        self.delay(delay_seconds)
        win32api.keybd_event(ord(key), win32api.MapVirtualKey(ord(key), 0), win32con.KEYEVENTF_KEYUP, 0)

    @on_mouse_focus
    def moveto(self, x, y):
        win32api.SetCursorPos((x, y))

    @on_mouse_focus
    def left_click(self, delay_seconds=0.01):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        self.delay(delay_seconds)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    @on_mouse_focus
    def mouse_wheel(self, pixel):
        """
            滚动鼠标滚轮
            Args:
                pixel: 滚动像素量。正数表示向上滚动，负数表示向下滚动。
        """
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, pixel, 0)


if __name__ == '__main__':
    import param
    c = Control(param.process_name)
    c.keypress("E")
    c.delay(1)
    c.interrupt()
    c.keypress("F")
    c.delay(3600)
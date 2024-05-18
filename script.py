import time, threading
from functools import partial
import keyboard
import config
import control
import param
from control import *
import utils


is_running = False
task_ctrls = {}
index = 0
lock = threading.Lock()


def bind_hotkey():
    @utils.new_thread
    def func():
        for type in param.type_handles.keys():
            keyboard.add_hotkey(config.bind_keys[type], partial(start_script, type))
        keyboard.add_hotkey(config.bind_keys['结束'], partial(stop_script))
        keyboard.wait()
    func()


def start_script(type):
    global is_running
    global index

    if is_running:
        print('[ERROR] 脚本不支持并发运行')
        return
    is_running = True

    lock.acquire()

    ctrl = control.Control(param.process_name)
    task_ctrls[index] = ctrl

    print(f'开始【{type}】演奏')

    @utils.new_thread
    def thread_func(index):
        global is_running
        try:
            script_body(ctrl, type)
            print(f'完成【{type}】演奏')
        except OperationInterrupt:
            print(f'中止【{type}】演奏')
            del task_ctrls[index]
        is_running = False

    thread_func(index)

    index += 1
    lock.release()


def stop_script():
    print('尝试中止所有演奏')
    global is_running
    for ctrl in task_ctrls.values():
        ctrl.interrupt()
    for type in param.type_handles.keys():
        param.type_handles[type]['stop']()
    is_running = False


def script_body(ctrl, type):
    c = ctrl

    while is_running:
        # 长按E 开始演奏 (可能会有bug，多重复几次吧)
        for i in range(12):
            c.keypress('E', 2)
        #c.delay(4)

        # 演奏几次
        times = 2
        for i in range(times):
            # 打开 曲艺手册
            c.moveto(1818, 241)
            c.delay(0.1)
            c.left_click()
            c.delay(1)

            # 曲艺手册 翻到最后
            c.moveto(996, 710)
            c.delay(0.5)
            c.mouse_wheel(-3000)
            c.delay(1)

            # 选择 《专家-天选》
            c.moveto(996, 710)
            c.delay(0.1)
            c.left_click()

            # 点击 开始演奏
            c.moveto(1689, 943)
            c.delay(0.1)
            c.left_click()

            # 演奏 并 等待演奏完成
            utils.new_thread(param.type_handles[type]['start'])(c)
            # 乐曲时长
            c.delay(3 * 60 + 24)
            c.delay(12)

            # 确认获取熟练度窗口，有时会出两次
            c.keypress(' ')
            c.delay(2)
            c.keypress(' ')
            c.delay(2)

        # 按esc起身
        c.keypress('\x1b')
        c.delay(3)
        # 确认获取熟练度窗口，有时这里也会出现
        c.keypress(' ')
        c.delay(5)

        # 小跳一下 (为了屏幕中显示 E 键)
        c.keypress(' ')
        c.delay(0.5)



if __name__ == '__main__':
    bind_hotkey()
    while True:
        time.sleep(3600)
import time, threading
from control import *
import utils
import script
import param


is_running = False
task_ctrls = {}
index = 0
lock = threading.Lock()


def start_script(mode, type):
    global is_running
    global index

    if is_running:
        print('[ERROR] 脚本不支持并发运行')
        return
    is_running = True

    lock.acquire()

    ctrl = Control(param.process_name)
    task_ctrls[index] = ctrl

    print(f'[{mode}模式] 开始【{type}】演奏')

    @utils.new_thread
    def loop_thread_func(index):
        global is_running
        try:
            script.loop_script_body(ctrl, mode, type)
            print(f'[{mode}模式] 完成【{type}】演奏')
        except OperationInterrupt:
            print(f'[{mode}模式] 中止【{type}】演奏')
            del task_ctrls[index]
        is_running = False

    @utils.new_thread
    def scan_thread_func(index):
        global is_running
        param.type_handles[type]['start'](ctrl, mode)
        del task_ctrls[index]
        is_running = False

    if mode == '循环':
        loop_thread_func(index)
    else:
        scan_thread_func(index)

    index += 1
    lock.release()


def stop_script(mode):
    print('尝试中止所有演奏操作')
    global is_running
    for ctrl in task_ctrls.values():
        ctrl.interrupt()
    for type in param.type_handles.keys():
        param.type_handles[type]['stop'](mode)
    is_running = False


def loop_script_body(ctrl, mode, type):
    c = ctrl

    while is_running:
        # 长按E 开始演奏 (可能会有bug，多重复几次吧)
        for i in range(10):
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
            utils.new_thread(param.type_handles[type]['start'])(ctrl, mode)
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
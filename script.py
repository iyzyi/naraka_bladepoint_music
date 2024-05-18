import asyncio, time
from functools import partial

import config
from control import *
import utils
import keyboard


is_running = False
tasks = {}
for type in config.bind_keys.keys():
    tasks[type] = None


def bind_hotkey():
    @utils.new_thread
    def func():
        for type in config.bind_keys.keys():
            keyboard.add_hotkey(config.bind_keys[type]['start'], partial(start_script, type))
            keyboard.add_hotkey(config.bind_keys[type]['stop'], partial(stop_script, type))
        keyboard.wait()
    func()


def start_script(type):
    print(f'快捷键: {config.bind_keys[type]["start"]}\t开始【{type}】演奏')

    global is_running
    if is_running:
        print('[ERROR] 脚本不支持并发运行')
        return
    is_running = True

    async def async_func(type):
        loop = asyncio.get_event_loop()
        task = loop.run_until_complete(script_body(type))
        tasks[type] = task

        # @utils.new_thread
        # def f(type):
        #     time.sleep(2)
        #     tasks[type].cancel()
        # #f(type)

        # await asyncio.sleep(2)
        # task.cancel()

        try:
            await task
            print('执行完成')
        except asyncio.CancelledError:
            print('执行终止')

    @utils.new_thread
    def thread_func():
        global is_running
        asyncio.run(async_func(type))
        is_running = False
        tasks[type] = None

    thread_func()


def stop_script(type):
    print(f'快捷键: {config.bind_keys[type]["stop"]}\t结束【{type}】演奏')
    global is_running
    if is_running:
        print('尝试终止')
        tasks[type].cancel()
        tasks[type] = None
        is_running = False


async def script_body(type):
    await asyncio.sleep(5)

    # try:
    #     print("Task started")
    #     await asyncio.sleep(5)
    #     print("Task completed")
    # except asyncio.CancelledError:
    #     print("Task cancelled")

    # # 长按E 开始演奏
    # await keypress('E', 1600)
    # await delay(4)
    #
    # # 演奏几次
    # times = 2
    # for i in range(times):
    #     # 打开 曲艺手册
    #     await moveto(1818, 241)
    #     await delay(0.1)
    #     await left_click()
    #     await delay(1)
    #
    #     # 曲艺手册 翻到最后
    #     await moveto(996, 710)
    #     await delay(0.1)
    #     await mouse_wheel(-300)
    #     await delay(0.5)
    #
    #     # 选择 《专家-天选》
    #     await moveto(996, 710)
    #     await delay(0.1)
    #     await left_click()
    #
    #     # 点击 开始演奏
    #     await moveto(1689, 943)
    #     await delay(0.1)
    #     await left_click()
    #
    #     # 演奏
    #
    #     # 退出


if __name__ == '__main__':
    bind_hotkey()
    while True:
        asyncio.run(delay(3600))
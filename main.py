import time
from functools import partial
import keyboard
import script
import config
import param
import utils


def bind_hotkey():
    @utils.new_thread
    def func():
        for mode in ['循环', '扫描']:
            for type in param.type_handles.keys():
                keyboard.add_hotkey(config.bind_keys[f'{mode}-{type}'], partial(script.start_script, mode, type))
        keyboard.add_hotkey(config.bind_keys['结束'], partial(script.stop_script, mode))
        keyboard.wait()
    func()


if __name__ == '__main__':
    print('欢迎使用永劫无间乐器熟练度速刷脚本')
    print('快捷键\t功能')
    for k, v in config.bind_keys.items():
        print(f'{v}\t\t{k}')
    print()

    bind_hotkey()

    while True:
        time.sleep(3600)
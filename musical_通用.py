import os, time, shutil, hashlib, threading, queue
import cv2
import numpy as np
import pyautogui
import config
import utils
import control
import script
import param
import param_通用


debug = False
temp_dir = r'D:\temp'
if debug and os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

images_queue = queue.Queue()
result_queue = queue.Queue()
is_running = False
queue_get_timeout = 1

long_press_image_path = r'images\long_press.jpg'
assert os.path.exists(long_press_image_path)
long_press_image = cv2.imread(long_press_image_path)
button_right_image_path = r'images\button_right.jpg'
assert os.path.exists(button_right_image_path)
button_right_image = cv2.imread(button_right_image_path)
long_press_image_height, long_press_image_width = long_press_image.shape[:-1]
button_right_image_height, button_right_image_width = button_right_image.shape[:-1]


# 裁剪图像、OCR
def crop_and_ocr(image, args, time_str, frame_index):
    x, y, width, height, type = args

    # 裁剪特定区域
    image = image[y:y+height, x:x+width]
    image_ori = image

    # 反转颜色
    image = 255 - image

    # 将图像转换为灰度图像
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 设定阈值，将灰度图像转换为黑白图像
    _, image = cv2.threshold(image, 75, 255, cv2.THRESH_BINARY)

    # 计算白色像素点的比例
    region = image
    white_count = np.count_nonzero(region == 255)
    total_pixels = height * width
    white_ratio = white_count / total_pixels
    #print(f'type: {type}\twhite_ratio: {white_ratio}')

    text = ''
    # OCR速度太慢了，通过这一条件屏蔽大部分无效图像
    if 0.5 < white_ratio < 0.95:
        text = utils.OCR(image)

        # if debug and temp_dir != '':
        #     temp = text
        #     if text == '':
        #         temp = 'null'
        #     cv2.imwrite(os.path.join(temp_dir, f'{frame_index}_{time_str}_{type}_{temp}.jpg'), image)
        #     cv2.imwrite(os.path.join(temp_dir, f'{frame_index}_{time_str}_{type}_{temp}_ori.jpg'), image_ori)

    # 计算图片哈希，用于判定目标区域画面无变化/重复插帧的情况
    image_bytes = cv2.imencode('.jpg', image)[1].tobytes()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    return (text, image_hash)


def screenshot_thread_func():
    frame_interval = 1.0 / param.fps
    frame_index = 0

    while is_running:
        begin = time.time()
        screenshot = pyautogui.screenshot()
        image = screenshot#cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        images_queue.put((frame_index, begin, image))
        frame_index += 1
        end = time.time()
        if (end - begin) < frame_interval:
            time.sleep(frame_interval - (end - begin))
        else:
            print('[WARNING] 无法满足所需帧数，可能会导致按键识别延迟')


def recognize_thread_func():
    global images_list

    while is_running:
        try:
            frame_index, timestamp, image = images_queue.get(timeout=queue_get_timeout)
        except queue.Empty:
            continue
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        if not utils.is_music_ui(image):
            continue
        time_str = utils.time2str(timestamp)
        res_top = crop_and_ocr(image, param_通用.args_top, time_str, frame_index)
        res_middle = crop_and_ocr(image, param_通用.args_middle, time_str, frame_index)
        res_bottom = crop_and_ocr(image, param_通用.args_bottom, time_str, frame_index)
        result_queue.put((frame_index, timestamp, image, res_top, res_middle, res_bottom))


def keypress_thread_func(ctrl):
    global result_list

    ack_index = -1
    last_index = 0
    last_press_index = 0

    last_hash_top = ''
    last_hash_middle = ''
    last_hash_bottom = ''

    last_key = ''
    last_key_top = ''
    last_key_middle = ''
    last_key_bottom = ''

    on_keydown_top = False
    on_keydown_middle = False
    on_keydown_bottom = False

    while is_running:
        try:
            result = result_queue.get(timeout=queue_get_timeout)
        except queue.Empty:
            continue
        frame_index, timestamp, image, res_top, res_middle, res_bottom = result

        non_null = 0
        for res in result[3:]:  # res: (text, hash)
            if res[0] != '':
                non_null += 1
        if non_null == 0:
            continue
        if non_null != 1:
            print(f'[WARNING] 多行均识别出非零值: {result}')
            continue

        num_top, hash_top = res_top
        num_middle, hash_middle = res_middle
        num_bottom, hash_bottom = res_bottom

        num = 0
        skip = False

        if num_top != '':
            if int(num_top) not in param_通用.map_top.keys():
                print(f'[WARNING] map_top中没有对应键: {num_top}')
                continue
            key = param_通用.map_top[int(num_top)]
            last_key = last_key_top
            num = num_top
            if last_hash_top == hash_top:
                last_index = frame_index
                skip = True
            last_hash_top = hash_top
        elif num_middle != '':
            if int(num_middle) not in param_通用.map_middle.keys():
                print(f'[WARNING] map_middle没有对应键: {num_middle}')
                continue
            key = param_通用.map_middle[int(num_middle)]
            last_key = last_key_middle
            num = num_middle
            if last_hash_middle == hash_middle:
                last_index = frame_index
                skip = True
            last_hash_middle = hash_middle
        else:
            if int(num_bottom) not in param_通用.map_bottom.keys():
                print(f'[WARNING] map_bottom中没有对应键: {num_bottom}')
                continue
            key = param_通用.map_bottom[int(num_bottom)]
            last_key = last_key_bottom
            num = num_bottom
            if last_hash_bottom == hash_bottom:
                last_index = frame_index
                skip = True
            last_hash_bottom = hash_bottom

        if skip:
            continue

        # 由于是多线程识别，所以如果当前按键位于已经确认的最新按键之前，则忽略
        if frame_index <= ack_index:
            continue

        # 相邻两帧不要都按下按键，因为第二帧的数字可能会卡在边界导致误识别
        # 比如是同一个按键，第一帧正确识别3，第二帧由于3被卡了一半，识别成1
        # 如果都响应，则会消耗下一次按键的正确机会，造成恶性循环
        if frame_index <= last_press_index + 1:
            continue

        # 相邻两帧可能对应的是同一次按键（比如分别位于切割区域的一左一右）
        if not (key != last_key or frame_index > last_index + 1):
            continue

        # 判断是否需要长按按键
        def judge_long_press(image, long_args):



            # 需要长按按键的情况的充要条件：
            # 1) 最左边的那个long_press图像 在 最左边的那个button_right图像的右边，且二者之间没有其他的button_right图像
            # 2) 最左边的那个button_right的x坐标不超过一定阈值
            def judge(long_press_coords, button_right_coords):
                index = 1
                for coord in button_right_coords:
                    if coord[0] < long_press_coords[0][0]:
                        index += 1
                if index == 2:
                    threshold = button_right_image_height
                    if button_right_coords[0][0] < threshold:
                        return True
                return False

            # 裁剪特定区域
            x, y, width, height = long_args
            image = image[y:y + height, x:x + width]

            long_press_coords = utils.image_search(image, long_press_image)
            # for coord in long_press_coords:
            #     cv2.rectangle(image, coord, (coord[0] + long_press_image_width, coord[1] + long_press_image_width), (0, 0, 255), 2)
            # print(long_press_coords)

            button_right_coords = utils.image_search(image, button_right_image)
            # for coord in button_right_coords:
            #     cv2.rectangle(image, coord, (coord[0] + button_right_image_width, coord[1] + button_right_image_height), (0, 0, 255), 2)
            # print(button_right_coords)

            if len(long_press_coords) > 0 and len(button_right_coords) > 0:
                result = judge(long_press_coords, button_right_coords)
                # if result and debug and temp_dir != '':
                #     cv2.imwrite(os.path.join(temp_dir, f'{frame_index}_long.jpg'), image)
                return result
            return False

        @utils.new_thread
        def custom_keypress(key, delay1, delay2):
            try:
                ctrl.delay(delay1)
                ctrl.keypress(key, delay2)
            except control.OperationInterrupt:
                stop()

        @utils.new_thread
        def custom_keydown(key, delay1):
            try:
                ctrl.delay(delay1)
                ctrl.keydown(key)
            except control.OperationInterrupt:
                stop()

        @utils.new_thread
        def custom_keyup(key, delay1):
            try:
                ctrl.delay(delay1)
                ctrl.keyup(key)
            except control.OperationInterrupt:
                stop()

        if num_top != '':
            judge_down = judge_long_press(image, param_通用.long_top)
            judge_up = key == last_key_top and on_keydown_top
        elif num_middle != '':
            judge_down = judge_long_press(image, param_通用.long_middle)
            judge_up = key == last_key_middle and on_keydown_middle
        else:
            judge_down = judge_long_press(image, param_通用.long_bottom)
            judge_up = key == last_key_bottom and on_keydown_bottom

        # 长按-up
        if judge_up:
            custom_keyup(key, config.key_delay['通用'])
            if num_top != '':
                on_keydown_top = False
            elif num_middle != '':
                on_keydown_middle = False
            else:
                on_keydown_bottom = False
            type = 'U'

        else:
            # 万一没识别到up的那个键，则在下一次之前，先up上一次的长按按键
            if num_top != '' and on_keydown_top:
                if on_keydown_top:
                    custom_keyup(last_key_top, config.key_delay['通用'])
                on_keydown_top = False
            elif num_middle != '':
                if on_keydown_middle:
                    custom_keyup(last_key_middle, config.key_delay['通用'])
                on_keydown_middle = False
            else:
                if on_keydown_bottom:
                    custom_keyup(last_key_bottom, config.key_delay['通用'])
                on_keydown_bottom = False

            # 长按-down
            if judge_down:
                custom_keydown(key, config.key_delay['通用'])
                if num_top != '':
                    on_keydown_top = True
                elif num_middle != '':
                    on_keydown_middle = True
                else:
                    on_keydown_bottom = True
                type = 'D'

            # 正常按键
            else:
                custom_keypress(key, config.key_delay['通用'], 0.01)
                type = 'P'

        print(f'{frame_index:08d}\t{utils.time2str(timestamp)}\t\t[{type}]\t{key}\t{num}')

        ack_index = frame_index
        last_index = frame_index
        last_press_index = frame_index
        if num_top != '':
            last_key_top = key
        elif num_middle != '':
            last_key_middle = key
        else:
            last_key_bottom = key


def start(ctrl):
    global is_running
    if is_running:
        print('[ERROR] 脚本不支持并发运行')
        return
    is_running = True

    # 截图线程
    screenshot_thread = threading.Thread(target=screenshot_thread_func)
    screenshot_thread.daemon = True
    screenshot_thread.start()

    # 识别线程
    recognize_threads = []
    for i in range(8):
        recognize_thread = threading.Thread(target=recognize_thread_func)
        recognize_thread.daemon = True
        recognize_threads.append(recognize_thread)
        recognize_thread.start()

    # 按键线程
    keypress_thread = threading.Thread(target=keypress_thread_func, args=(ctrl,))
    keypress_thread.daemon = True
    keypress_thread.start()

    # 阻塞主线程
    screenshot_thread.join()
    for recognize_thread in recognize_threads:
        recognize_thread.join()
    keypress_thread.join()

    is_running = False


def stop():
    global is_running
    if is_running:
        print(f'[{script.g_mode}模式] 中止【通用】演奏')
    is_running = False


if __name__ == '__main__':
    ctrl = control.Control(param.process_name)
    start(ctrl)

import os, time, shutil, hashlib, threading, queue
import cv2
import numpy as np
import pyautogui
import pytesseract
import config
import utils
import control
import script
import param
import param_通用


debug = True
temp_dir = r'D:\temp'
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

images_queue = queue.Queue()
result_queue = queue.Queue()
is_running = False
queue_get_timeout = 1

long_press_image = cv2.imread(r'image\long_press.jpg')
button_right_image = cv2.imread(r'd:\Snipaste_2024-05-24_17-43-34.jpg')
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
        # --psm 7 单行识别
        # --oem 3 使用 LSTM OCR 引擎
        # -c tessedit_char_whitelist=0123456789 只识别数字字符
        text = pytesseract.image_to_string(image, config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
        text = text.strip()

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

        # 判断是否需要长按、计算长按时间
        def calc_long_press_delay(image, long_args):
            if config.long_press_k == 0:
                return control.default_delay

            def image_search(image, target):
                # 搜图
                res = cv2.matchTemplate(image, target, cv2.TM_CCOEFF_NORMED)
                threshold = 0.8
                loc = np.where(res >= threshold)
                coords = [coord for coord in zip(*loc[::-1])]

                # 去重
                temp = []
                threshold = 10
                for coord in coords:
                    exists = False
                    for coord2 in temp:
                        if abs(coord[0] - coord2[0]) <= threshold and abs(coord[1] - coord2[1]) <= threshold:
                            exists = True
                    if not exists:
                        temp.append(coord)
                coords = sorted(temp, key=lambda pair: pair[0])
                return coords

            def calc_long_press_pixels(long_press_coords, button_right_coords):
                index = 1
                for coord in button_right_coords:
                    if coord[0] < long_press_coords[0][0]:
                        index += 1
                if index == 2:
                    threshold = button_right_image_height
                    if button_right_coords[0][0] < threshold:
                        return 2 * (long_press_coords[0][0] + long_press_image_width // 2 -
                                    (button_right_coords[0][0] + button_right_image_width))
                return 0

            # 裁剪特定区域
            x, y, width, height = long_args
            image = image[y:y + height, x:x + width]

            long_press_coords = image_search(image, long_press_image)
            # for coord in long_press_coords:
            #     cv2.rectangle(image, coord, (coord[0] + long_press_image_width, coord[1] + long_press_image_width), (0, 0, 255), 2)
            # print(long_press_coords)

            button_right_coords = image_search(image, button_right_image)
            # for coord in button_right_coords:
            #     cv2.rectangle(image, coord, (coord[0] + button_right_image_width, coord[1] + button_right_image_height), (0, 0, 255), 2)
            # print(button_right_coords)

            if len(long_press_coords) > 0 and len(button_right_coords) > 0:
                pixels = calc_long_press_pixels(long_press_coords, button_right_coords)
                if pixels != 0:
                    # if debug and temp_dir != '':
                    #     cv2.imwrite(os.path.join(temp_dir, f'{frame_index}_long_{pixels}.jpg'), image)\

                    #delay = pixels * (config.keypress_delay['通用'] / param_通用.pixels)
                    # 不能直接像上面那样直接按比例转换像素对应的时间，因为 param_通用.pixels 中有一部分像素对应的时间消耗在处理、识别图像上
                    delay = pixels * (config.keypress_delay['通用'] / param_通用.pixels) * config.long_press_k
                    return delay

            # 正常按下按键，不长按
            return control.default_delay

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
            delay = calc_long_press_delay(image, param_通用.long_top)
            judge_up = key == last_key_top and on_keydown_top
        elif num_middle != '':
            delay = calc_long_press_delay(image, param_通用.long_middle)
            judge_up = key == last_key_middle and on_keydown_middle
        else:
            delay = calc_long_press_delay(image, param_通用.long_bottom)
            judge_up = key == last_key_bottom and on_keydown_bottom

        if delay != control.default_delay:
            custom_keydown(key, config.keypress_delay['通用'])
            if num_top != '':
                on_keydown_top = True
            elif num_middle != '':
                on_keydown_middle = True
            else:
                on_keydown_bottom = True
            type = 'D'

        elif judge_up:
            custom_keyup(key, config.keypress_delay['通用'])
            if num_top != '':
                on_keydown_top = False
            elif num_middle != '':
                on_keydown_middle = False
            else:
                on_keydown_bottom = False
            type = 'P'

        else:
            custom_keypress(key, config.keypress_delay['通用'], 0.01)
            type = 'U'

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

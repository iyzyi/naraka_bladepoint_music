import os, time, shutil, hashlib, threading, queue
import cv2
import numpy as np
import pyautogui
import pytesseract
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
        #     #cv2.imwrite(os.path.join(temp_dir, f'{frame_index}_{time_str}_{type}_{temp}_ori.jpg'), image_ori)

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
        image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        images_queue.put((frame_index, begin, image))
        frame_index += 1
        end = time.time()
        if (end - begin) < frame_interval:
            time.sleep(frame_interval - (end - begin))


def recognize_thread_func():
    global images_list

    while is_running:
        try:
            frame_index, timestamp, image = images_queue.get(timeout=queue_get_timeout)
        except queue.Empty:
            continue
        time_str = utils.time2str(timestamp)
        res_top = crop_and_ocr(image, param_通用.args_top, time_str, frame_index)
        res_middle = crop_and_ocr(image, param_通用.args_middle, time_str, frame_index)
        res_bottom = crop_and_ocr(image, param_通用.args_bottom, time_str, frame_index)
        result_queue.put((frame_index, timestamp, res_top, res_middle, res_bottom))


def keypress_thread_func(ctrl):
    global result_list
    ack_index = -1
    last_index = 0
    last_press_index = 0
    last_key = ''
    last_hash_top = ''
    last_hash_middle = ''
    last_hash_bottom = ''

    while is_running:
        try:
            result = result_queue.get(timeout=queue_get_timeout)
        except queue.Empty:
            continue
        frame_index, timestamp, res_top, res_middle, res_bottom = result

        non_null = 0
        for res in result[2:]:  # res: (text, hash)
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
        if key != last_key or frame_index > last_index + 1:
            @utils.new_thread
            def custom_keypress(key, delay1, delay2):
                try:
                    ctrl.delay(delay1)
                    ctrl.keypress(key, delay2)
                except control.OperationInterrupt:
                    stop()
            custom_keypress(key, 0.28, 0.01)
            print(f'{frame_index:08d}\t{utils.time2str(timestamp)}\t\t{key}\t{num}')

            ack_index = frame_index
            last_index = frame_index
            last_press_index = frame_index
            last_key = key


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

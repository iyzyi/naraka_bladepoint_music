import os, time, shutil, datetime, hashlib, threading, queue
import cv2
import numpy as np
import pyautogui
import pytesseract
import control, utils

debug = True
temp_dir = r'D:\temp'
shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

images_queue = queue.Queue()
result_queue = queue.Queue()


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

        if debug and temp_dir != '':
            temp = text
            if text == '':
                temp = 'null'
            cv2.imwrite(os.path.join(temp_dir, f'{frame_index}_{time_str}_{type}_{temp}.jpg'), image)
            #cv2.imwrite(os.path.join(temp_dir, f'{time_str}_{type}_{temp}_ori.jpg'), image_ori)

    # 计算图片哈希，用于判定目标区域画面无变化/重复插帧的情况
    image_bytes = cv2.imencode('.jpg', image)[1].tobytes()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    return (text, image_hash)


def screenshot_thread_func(fps):
    frame_interval = 1.0 / fps
    frame_index = 0

    while True:
        begin = time.time()
        screenshot = pyautogui.screenshot()
        image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        images_queue.put((frame_index, begin, image))
        frame_index += 1
        end = time.time()
        if (end - begin) < frame_interval:
            time.sleep(frame_interval - (end - begin))


def recognize_thread_func(args_top, args_middle, args_bottom):
    global images_list

    while True:
        frame_index, timestamp, image = images_queue.get()
        time_str = utils.time2str(timestamp)
        res_top = crop_and_ocr(image, args_top, time_str, frame_index)
        res_middle = crop_and_ocr(image, args_middle, time_str, frame_index)
        res_bottom = crop_and_ocr(image, args_bottom, time_str, frame_index)
        result_queue.put((frame_index, timestamp, res_top, res_middle, res_bottom))


def keypress_thread_func(map_top, map_middle, map_bottom):
    global result_list
    ack_index = -1
    last_index = 0
    last_press_index = 0
    last_key = ''
    last_hash_top = ''
    last_hash_middle = ''
    last_hash_bottom = ''

    while True:
        result = result_queue.get()
        frame_index, timestamp, res_top, res_middle, res_bottom = result

        non_null = 0
        for res in result[2:]:  # res: (text, hash)
            if res[0] != '':
                non_null += 1
        if non_null == 0:
            continue
        if non_null != 1:
            print(f'[ERROR] 多行均识别出非零值: {result}')
            continue

        num_top, hash_top = res_top
        num_middle, hash_middle = res_middle
        num_bottom, hash_bottom = res_bottom

        num = 0
        skip = False

        if num_top != '':
            if int(num_top) not in map_top.keys():
                print(f'[ERROR] map_top中没有对应键: {num_top}')
                continue
            key = map_top[int(num_top)]
            num = num_top
            if last_hash_top == hash_top:
                last_index = frame_index
                skip = True
            last_hash_top = hash_top
        elif num_middle != '':
            if int(num_middle) not in map_middle.keys():
                print(f'[ERROR] map_middle没有对应键: {num_middle}')
                continue
            key = map_middle[int(num_middle)]
            num = num_middle
            if last_hash_middle == hash_middle:
                last_index = frame_index
                skip = True
            last_hash_middle = hash_middle
        else:
            if int(num_bottom) not in map_bottom.keys():
                print(f'[ERROR] map_bottom中没有对应键: {num_bottom}')
                continue
            key = map_bottom[int(num_bottom)]
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
            control.keypress(key, 0.28, 0.01, 0)
            print(f'{frame_index:08d}\t{utils.time2str(timestamp)}\t\t{key}\t{num}')
            ack_index = frame_index
            last_index = frame_index
            last_press_index = frame_index
            last_key = key



def main(fps, recognize_thread_num, args_top, args_middle, args_bottom, map_top, map_middle, map_bottom):
    # 截图线程
    screenshot_thread = threading.Thread(target=screenshot_thread_func, args=(fps,))
    screenshot_thread.daemon = True
    screenshot_thread.start()

    # 识别线程
    recognize_threads = []
    for i in range(recognize_thread_num):
        recognize_thread = threading.Thread(target=recognize_thread_func, args=(args_top, args_middle, args_bottom,))
        recognize_thread.daemon = True
        recognize_threads.append(recognize_thread)
        recognize_thread.start()

    # 按键线程
    keypress_thread = threading.Thread(target=keypress_thread_func, args=(map_top, map_middle, map_bottom,))
    keypress_thread.daemon = True
    keypress_thread.start()

    # 阻塞主线程
    screenshot_thread.join()
    for recognize_thread in recognize_threads:
        recognize_thread.join()
    keypress_thread.start()



if __name__ == '__main__':
    fps = 20
    recognize_thread_num = 8

    x = 538 + 120
    width = 28
    height = 23
    args_top =  (x, 145, width, height, 'top')
    args_middle = (x, 240, width, height, 'middle')
    args_bottom = (x, 335, width, height, 'bottom')

    map_top = {1: 'Q', 2: 'W', 3: 'E', 4: 'R', 5: 'T', 6: 'Y', 7: 'U'}
    map_middle = {1: 'A', 2: 'S', 3: 'D', 4: 'F', 5: 'G', 6: 'H', 7: 'J'}
    map_bottom = {1: 'Z', 2: 'X', 3: 'C', 4: 'V', 5: 'B', 6: 'N', 7: 'M'}

    main(fps, recognize_thread_num, args_top, args_middle, args_bottom, map_top, map_middle, map_bottom)

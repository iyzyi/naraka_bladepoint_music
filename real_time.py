import os, time, datetime, hashlib
import cv2
import numpy as np
import pyautogui
import pytesseract
#import keyboard
#from pywinauto.keyboard import send_keys
#import pydirectinput
import win32api, win32con


# 计算图片哈希，用于判定重复插帧/目标区域画面无变化的情况
def calculate_image_md5(image_array):
    image_bytes = cv2.imencode('.jpg', image_array)[1].tobytes()
    return hashlib.md5(image_bytes).hexdigest()


# 裁剪图像、OCR
def crop_and_ocr(image, args, temp_dir='', debug=False):
    x, y, width, height, type = args

    # 裁剪特定区域
    image = image[y:y+height, x:x+width]

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
    # if debug:
    #     print(f'type: {type}\twhite_ratio: {white_ratio}')

    text = '' 
    # OCR速度太慢了，通过这一条件屏蔽大部分无效数据
    if white_ratio < 0.95:
        # --psm 7 单行识别 , --oem 3 使用 LSTM OCR 引擎 , -c tessedit_char_whitelist=0123456789 只识别数字字符
        text = pytesseract.image_to_string(image, config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
        text = text.strip()
        # if debug and text != '':
        #     print(text)

    image_hash = calculate_image_md5(image)

    if debug and temp_dir != '':
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        now = datetime.datetime.now()
        now_str = now.strftime('%Y-%m-%d_%H-%M-%S_%f')
        #print(now_str)
        #cv2.imwrite(os.path.join(temp_dir, f'{now_str}_{type}.jpg'), image)

    return (text, image_hash)


# 截图、OCR
def screenshot_and_judge(args_top, args_middle, args_bottom, temp_dir='', debug=False):
    screenshot = pyautogui.screenshot()
    image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    res_top = crop_and_ocr(image, args_top, temp_dir, debug)
    res_middle = crop_and_ocr(image, args_middle, temp_dir, debug)
    res_bottom = crop_and_ocr(image, args_bottom, temp_dir, debug)

    return res_top, res_middle, res_bottom


def key_press(key):
    # key实际上应为VK_CODE，这里我用不到
    win32api.keybd_event(ord(key), win32api.MapVirtualKey(ord(key), 0), 0, 0)
    time.sleep(.05)
    win32api.keybd_event(ord(key), win32api.MapVirtualKey(ord(key), 0), win32con.KEYEVENTF_KEYUP, 0)


def run(args_top, args_middle, args_bottom, map_top, map_middle, map_bottom, temp_dir='', debug=False):   
    index = 0
    last_index = 0
    last_key = 0
    last_hash_top = 0
    last_hash_middle = 0
    last_hash_bottom = 0

    while True:
        index += 1

        result = screenshot_and_judge(args_top, args_middle, args_bottom, temp_dir, debug)
        non_null = 0
        for temp in result:    # temp: (text, hash)
            if temp[0] != '':
                non_null += 1
        if non_null == 0:
            continue
        if non_null != 1:
            print(f'[ERROR] 多行有效: {result}')
            continue
        
        num_top, hash_top = result[0]
        num_middle, hash_middle = result[1]
        num_bottom, hash_bottom = result[2]

        num = 0
        skip = False
        try:   
            if num_top != '':
                key = map_top[int(num_top)]
                num = num_top
                if last_hash_top == hash_top:
                    last_index = index
                    skip = True
                last_hash_top = hash_top
            elif num_middle != '':
                key = map_middle[int(num_middle)]
                num = num_middle
                if last_hash_middle == hash_middle:
                    last_index = index
                    skip = True
                last_hash_middle = hash_middle
            else:
                key = map_bottom[int(num_bottom)]
                num = num_bottom
                if last_hash_bottom == hash_bottom:
                    last_index = index
                    skip = True
                last_hash_bottom = hash_bottom
        except KeyError as e:
            #print(f'[ERROR] {result}')
            continue

        if skip:
            continue

        # 相邻两帧可能对应的是同一次按键（分别位于切割区域的一左一右）
        if key != last_key or index > last_index + 1:
            key_press(key)
            print(index, key, num, last_index, last_key)
            last_key = key
            last_index = index



if __name__ == '__main__':
    x = 538
    width = 28
    height = 23
    args_top =  (x, 145, width, height, 'top')
    args_middle = (x, 240, width, height, 'middle')
    args_bottom = (x, 335, width, height, 'bottom')

    map_top = {1: 'Q', 2: 'W', 3: 'E', 4: 'R', 5: 'T', 6: 'Y', 7: 'U'}
    map_middle = {1: 'A', 2: 'S', 3: 'D', 4: 'F', 5: 'G', 6: 'H', 7: 'J'}
    map_bottom = {1: 'Z', 2: 'X', 3: 'C', 4: 'V', 5: 'B', 6: 'N', 7: 'M'}
    
    temp_dir = r'd:\temp'

    run(args_top, args_middle, args_bottom, map_top, map_middle, map_bottom, temp_dir, debug=True)
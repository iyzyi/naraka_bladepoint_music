import time, threading, os
import pytesseract
import cv2
import numpy as np
import config


music_ui_image_path = r'images\perfect.jpg'
assert os.path.exists(music_ui_image_path)
music_ui_image = cv2.imread(music_ui_image_path)


def new_thread(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
    return wrapper


def time2str(timestamp):
    return time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(timestamp)) + f'_{int(timestamp * 1000) % 1000:03d}'


def OCR(image):
    pytesseract.pytesseract.tesseract_cmd = config.tesseract_path
    # --psm 7 单行识别
    # --oem 3 使用 LSTM OCR 引擎
    # -c tessedit_char_whitelist=0123456789 只识别数字字符
    text = pytesseract.image_to_string(image, config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
    text = text.strip()
    return text


# 在image中搜索是否包含target，返回按x排序的(x, y)列表
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


def is_music_ui(image):
    res = image_search(image, music_ui_image)
    return len(res) > 0


if __name__ == '__main__':
    print(time2str(time.time()))
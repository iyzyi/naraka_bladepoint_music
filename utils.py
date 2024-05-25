import time, threading
import pytesseract
import config


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


if __name__ == '__main__':
    print(time2str(time.time()))
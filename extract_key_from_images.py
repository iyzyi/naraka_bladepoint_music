import os, re, pickle, hashlib
import cv2
import pytesseract
import numpy as np


# 计算图片哈希，用于判定重复插帧/目标区域画面无变化的情况
def calculate_image_md5(image_array):
    image_bytes = cv2.imencode('.jpg', image_array)[1].tobytes()
    return hashlib.md5(image_bytes).hexdigest()


# 裁剪图像、OCR
def crop_and_ocr(image_path, image, args, debug=False):
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
    if debug:
        print(f'{image_path}\t{type}\t{white_ratio}')

    text = '' 
    # OCR速度太慢了，通过这一条件屏蔽大部分无效数据
    if white_ratio < 0.95:
        # --psm 7 单行识别 , --oem 3 使用 LSTM OCR 引擎 , -c tessedit_char_whitelist=0123456789 只识别数字字符
        text = pytesseract.image_to_string(image, config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789')
        text = text.strip()
        if debug and text != '':
            print(text)

    image_hash = calculate_image_md5(image)

    if debug:
        cv2.imwrite(image_path+f'.{type}.jpg', image)
        
    #cv2.imwrite(r'd:\test.jpg', image)
    return (text, image_hash)


def extract_key_from_images(images_dir, args_top, args_middle, args_bottom, debug=False):
    data = {}

    for image_name in os.listdir(images_dir):
        res = re.search(r'^(\d{8}).jpg$', image_name)
        if not res:
            continue
        
        index = int(res.group(1), 10)
        if index % 100 == 0:
            print(index)

        image_path = os.path.join(images_dir, image_name)
        image = cv2.imread(image_path)
        if image is None:
            print('无法读取图像')
            break

        res_top = crop_and_ocr(image_path, image, args_top, debug)
        res_middle = crop_and_ocr(image_path, image, args_middle, debug)
        res_bottom = crop_and_ocr(image_path, image, args_bottom, debug)
        
        data[index] = (res_top, res_middle, res_bottom)

    with open(r'data.pickle', 'wb')as f:
        pickle.dump(data, f)


def convert_script_by_key(map_top, map_middle, map_bottom, fps):
    with open('data.pickle', 'rb')as f:
        data = pickle.load(f)
    
    script = ''
    last_index = 0
    last_press_index = 0
    last_key = 0
    last_hash_top = 0
    last_hash_middle = 0
    last_hash_bottom = 0

    for index in sorted(data.keys()):
        non_null = 0
        for temp in data[index]:    # temp: (text, hash)
            if temp[0] != '':
                non_null += 1
        if non_null == 0:
            continue
        if non_null != 1:
            print(f'[ERROR] 多行有效: {data[index]}')
            exit()

        num_top, hash_top = data[index][0]
        num_middle, hash_middle = data[index][1]
        num_bottom, hash_bottom = data[index][2]

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
            print(f'[ERROR] index: {index}, data: {data[index]}')
            continue

        if skip:
            continue
        
        # 相邻两帧可能对应的是同一次按键（分别位于切割区域的一左一右）
        if key != last_key or index > last_index + 1:
            delay = int((index - last_press_index) * (1000 / fps) - 10 - 8)
            script += f'\nDelay {delay}\nKeyDown "{key}", 1\nDelay 10\nKeyUp "{key}", 1\n'
            #script += f'\nDelay {delay}\nKeyPress "{key}", 1'
            #print(index, key, num, last_index, last_key)
            last_key = key
            last_index = index
            last_press_index = index

    with open('script.txt', 'w')as f:
        f.write(script)



if __name__ == '__main__':
    images_dir = r'D:\yjwj_music\images\guqin-part1'

    x = 538
    width = 28
    height = 23
    args_top =  (x, 145, width, height, 'top')
    args_middle = (x, 240, width, height, 'middle')
    args_bottom = (x, 335, width, height, 'bottom')
    #extract_key_from_images(images_dir, args_top, args_middle, args_bottom, debug=True)
    
    
    map_top = {1: 'Q', 2: 'W', 3: 'E', 4: 'R', 5: 'T', 6: 'Y', 7: 'U'}
    map_middle = {1: 'A', 2: 'S', 3: 'D', 4: 'F', 5: 'G', 6: 'H', 7: 'J'}
    map_bottom = {1: 'Z', 2: 'X', 3: 'C', 4: 'V', 5: 'B', 6: 'N', 7: 'M'}
    fps = 20
    convert_script_by_key(map_top, map_middle, map_bottom, fps)



    # image_path = r'D:\桌面\yjwj_music\test'
    # image = cv2.imread(image_path)
    # if image is None:
    #     print('无法读取图像')
    #     break
    # text_middle = crop_and_ocr(image, args_middle, debug)
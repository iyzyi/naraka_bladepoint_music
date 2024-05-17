
截图、OCR
def screenshot_and_judge(args_top, args_middle, args_bottom, temp_dir='', debug=False):
    screenshot = pyautogui.screenshot()
    image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    now = datetime.datetime.now()
    time_str = now.strftime('%Y-%m-%d_%H-%M-%S_%f')
    print(time_str)

    res_top = crop_and_ocr(image, args_top, time_str, temp_dir)
    res_middle = crop_and_ocr(image, args_middle, time_str, temp_dir)
    res_bottom = crop_and_ocr(image, args_bottom, time_str, temp_dir)

    return res_top, res_middle, res_bottom


def run(args_top, args_middle, args_bottom, map_top, map_middle, map_bottom):
    shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    index = 0
    last_index = 0
    last_key = 0
    last_hash_top = 0
    last_hash_middle = 0
    last_hash_bottom = 0

    while True:
        index += 1
        begin = time.time()

        result = screenshot_and_judge(args_top, args_middle, args_bottom)
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
            control.key_press(key)
            times = f'{int((time.time() - begin) * 1000)}ms'
            print(times, index, key, num, last_index, last_key)
            last_key = key
            last_index = index

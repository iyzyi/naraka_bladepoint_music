# 绑定按键
bind_keys = {
    '扫描-古筝':    'f3',
    '扫描-通用':    'f4',  # 二胡、曲笛、唢呐
    '扫描-疆鼓':    'f5',
    '扫描-梆子':    'f6',
    '扫描-锣':     'f7',

    '循环-古筝':    'f8',
    '循环-通用':    'f9',
    '循环-疆鼓':    'f10',
    '循环-梆子':    'f11',
    '循环-锣':     'f12',

    '结束':         'f1'
}

# 扫描模式：
# 没有其他操作，纯粹地扫描画面，根据OCR结果，按下对应按键。

# 循环模式：
# 站在乐器旁边，屏幕中需要显示E键。
# 开启后，自动选择《专家-天选》进行演奏。
# 每演奏一曲，都会调用一次扫描模式。
# 演奏两次后退出，然后重复以上流程。


import yaml
data = yaml.load(open('config.yaml', encoding='utf-8').read(), Loader=yaml.FullLoader)
key_delay = data['key_delay']
tesseract_path = data['tesseract_path']
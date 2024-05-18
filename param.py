import musical_通用

# 进程名称
process_name = "NarakaBladepoint.exe"

# 每秒截取最大帧数
fps = 20


def passs():
    pass

# 不同乐器的处理函数
type_handles = {
    '通用': {'start': musical_通用.start, 'stop': musical_通用.stop},
    '疆鼓': {'start': passs, 'stop': passs},
    '梆子': {'start': passs, 'stop': passs},
    '锣': {'start': passs, 'stop': passs},
}

import musical_通用

# 进程名称
process_name = "NarakaBladepoint.exe"

# 每秒截取最大帧数
fps = 20

# 通用
x = 538 + 120
width = 28
height = 23
args_top =  (x, 145, width, height, 'top')
args_middle = (x, 240, width, height, 'middle')
args_bottom = (x, 335, width, height, 'bottom')

map_top = {1: 'Q', 2: 'W', 3: 'E', 4: 'R', 5: 'T', 6: 'Y', 7: 'U'}
map_middle = {1: 'A', 2: 'S', 3: 'D', 4: 'F', 5: 'G', 6: 'H', 7: 'J'}
map_bottom = {1: 'Z', 2: 'X', 3: 'C', 4: 'V', 5: 'B', 6: 'N', 7: 'M'}



def passs():
    pass

type_handles = {
    '通用': {'start': musical_通用.start, 'stop': musical_通用.stop},    # 古筝、二胡、曲笛、唢呐
    '疆鼓': {'start': passs, 'stop': passs},
    '梆子': {'start': passs, 'stop': passs},
    '锣': {'start': passs, 'stop': passs},
}

# 通用: 二胡、曲笛、唢呐

pixels = 120
x = 538 + pixels
width = 28
height = 23

args_top = (x, 145, width, height, 'top')
args_middle = (x, 240, width, height, 'middle')
args_bottom = (x, 335, width, height, 'bottom')

map_top = {1: 'Q', 2: 'W', 3: 'E', 4: 'R', 5: 'T', 6: 'Y', 7: 'U'}
map_middle = {1: 'A', 2: 'S', 3: 'D', 4: 'F', 5: 'G', 6: 'H', 7: 'J'}
map_bottom = {1: 'Z', 2: 'X', 3: 'C', 4: 'V', 5: 'B', 6: 'N', 7: 'M'}

# 用于判断/计算长按按键相关
long_width = 1000
long_height = 56
long_top = (x, 135, long_width, long_height)
long_middle = (x, 232, long_width, long_height)
long_bottom = (x, 327, long_width, long_height)
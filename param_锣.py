x = 538 + 120 - 10  # 因为下一行，所以这里需要前移
width = 28 + 10     # 因为有两位数的10~13，所以增加一些匹配区域
height = 23

args_top = (x, 145, width, height, 'top')
args_middle = (x, 240, width, height, 'middle')
args_bottom = (x, 335, width, height, 'bottom')

map_top = {9: 'E', 10: 'R', 11: 'T', 12: 'Y', 13: 'U'}
map_middle = {5: 'D', 6: 'F', 7: 'H', 8: 'J'}
map_bottom = {1: 'C', 2: 'V', 3: 'N', 4: 'M'}
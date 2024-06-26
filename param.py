import musical_古筝
import musical_通用
import musical_疆鼓
import musical_梆子
import musical_锣

# 进程名称
process_name = "NarakaBladepoint.exe"

# 每秒截取最大帧数
fps = 20

# 扫描模式下，不同乐器的处理函数
type_handles = {
    '古筝': {'start': musical_古筝.start, 'stop': musical_古筝.stop},
    '通用': {'start': musical_通用.start, 'stop': musical_通用.stop},
    '疆鼓': {'start': musical_疆鼓.start, 'stop': musical_疆鼓.stop},
    '梆子': {'start': musical_梆子.start, 'stop': musical_梆子.stop},
    '锣': {'start': musical_锣.start, 'stop': musical_锣.stop},
}

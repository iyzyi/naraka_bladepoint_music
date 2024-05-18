import time, threading


def new_thread(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
    return wrapper


def time2str(timestamp):
    return time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(timestamp)) + f'_{int(timestamp * 1000) % 1000:03d}'


if __name__ == '__main__':
    print(time2str(time.time()))
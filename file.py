import asyncio, time
import threading

task = None


async def async_task():
    begin = time.time()
    try:
        await asyncio.sleep(5)
        # while True:
        #     print("Async task is running...")
        #     await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Async task is cancelled.")
    finally:
        end = time.time()
        print(end - begin)

async def start_async_task():
    global task
    # task = asyncio.create_task(async_task())
    # await task
    loop = asyncio.get_event_loop()
    #loop.call_soon(my_callback)
    loop.run_until_complete(async_task())

def cancel_async_task():
    task.cancel()

def main():
    asyncio.run(start_async_task())

if __name__ == "__main__":
    # 启动异步任务的线程
    async_thread = threading.Thread(target=main)
    async_thread.start()

    # 模拟一段时间后取消任务的执行
    threading.Timer(1, cancel_async_task).start()


from concurrent import futures
from concurrent.futures import FIRST_EXCEPTION,as_completed
import random
import time
import sys
from multiprocessing import Event
import threading
import os

def init_worker(event):
    global shared_event
    shared_event = event

def get_request(url):
    time.sleep(2)
    print("start:", url)
    if "baidu" in url:
        print("error:", url)
        raise RuntimeError("error")
    time.sleep(10)
    print("url:",url)
    return url


class MyThread(threading.Thread):
    def run(self):
        try:
            threading.Thread.run(self)
        except Exception as err:
            self.err = err
            pass # or raise err
        else:
            self.err = None



def worker(fn,*args,**kwargs):
    thread = MyThread(target=fn, args=args, kwargs=kwargs)
    thread.start()
    while True:
        if shared_event.is_set():
            print("some thing get wrong...")
            os.system("kill -9 %d" % os.getpid())
        if not thread.is_alive():
            print("thread is not alive")
            if thread.err is not None:
                shared_event.set()
            break
        time.sleep(0.1)


#    return 100
urls = ['https://www.baidu.com','https://www.tmall.com','https://www.jd.com']
with futures.ProcessPoolExecutor(max_workers = 3,initializer=init_worker,initargs=(Event(),)) as pool:
    tasks = []
    for url in urls:
        future = pool.submit(worker, get_request,url)
        future.url = url
        tasks.append(future)
    for f in as_completed(tasks):
        print(f.result())
    # done, not_done =futures.wait(tasks, return_when=FIRST_EXCEPTION)
    # for f in done:
    #     print(f.result())
    # while True:
    #     for future in tasks:
    #         if future.done():
    #             print(future.__dict__)
    #             print("future._exception",future._exception)
    #             if future._exception:
    #                 raise future._exception
    #             tasks.remove(future)
    #             print('close task',future._exception)
    #     if not tasks:
    #         break

    #     time.sleep(1)
    # for future in tasks:
    #     print(future.result())
    # done,not_done = futures.wait(tasks,return_when=FIRST_EXCEPTION)
    # for f in done:
    #     print(f.result())

    # for f in done:
    #     print(f.__dict__)
        # print(f.result())
    # 处理已完成的任务
    # for future in done:
    #     try:
    #         result = future.result()
    #         print(result)
    #     except Exception as e:
    #         print(f"Task generated an exception: {e}")

    # # 如果有未完成的任务，可以选择取消它们
    # for future in not_done:
    #     future.cancel()



# SuperFastPython.com
# example of canceling all tasks if one task fails with an exception
# from random import random
# from time import sleep
# from multiprocessing.pool import Pool
# from multiprocessing import Manager

# # initialize worker processes
# def init_worker(shared_event):
#     # store the event as a global in the worker process
#     global event
#     event = shared_event

# # task executed in a worker process
# def task(identifier):
#     # loop for a while
#     for i in range(4):
#         # check for stop
#         if event.is_set():
#             print(f'Task {identifier} stopped', flush=True)
#             return
#         # block for a moment
#         sleep(random())
#         # conditionally fail
#         if i > 2 and identifier == 5:
#             print('Something bad happened!', flush=True)
#             # cancel all tasks
#             event.set()
#             return
#     # report done
#     print(f'Task {identifier} done', flush=True)

# # protect the entry point
# if __name__ == '__main__':
#     # create a manager
#     with Manager() as manager:
#         # create a shared event
#         shared_event = manager.Event()
#         # create and configure the process pool
#         with Pool(initializer=init_worker, initargs=(shared_event,)) as pool:
#             # issue tasks into the process pool
#             result = pool.map_async(task, range(10))
#             # wait for tasks to complete
#             result.wait()
        # process pool is closed automatically

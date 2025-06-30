import time

from imports import *
from backend.backMain import run_flask
from frontend.frontMain import run_webview
from database.dataMain import *


if __name__ == '__main__':
    multiprocessing.freeze_support()

    manager = multiprocessing.Manager()
    event_main = manager.dict()
    event_main["rides_exit"] = manager.Event()
    event_main["flask_exit"] = manager.Event()

    # redis_process = multiprocessing.Process(target=run_database_rides, args =(event_main,))
    # redis_process.start()
    flask_process = multiprocessing.Process(target=run_flask, args=(event_main,))
    flask_process.start()

    webview_process = multiprocessing.Process(target=run_webview)
    webview_process.start()
    webview_process.join()

    # 逆序清除进程(此处不要强制清理，进程函数应该编写为自给自足，完全可以自行清理)
    event_main["rides_exit"].set()
    event_main["flask_exit"].set()
    flask_process.join()
    # redis_process.join()

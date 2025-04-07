import time

from imports import *
from backend.backMain import run_flask
from frontend.frontMain import run_webview
from database.dataMain import *

if __name__ == '__main__':
    multiprocessing.freeze_support()
    redis_process = multiprocessing.Process(target=run_database_rides)
    redis_process.start()
    flask_process = multiprocessing.Process(target=run_flask)
    flask_process.start()
    webview_process = multiprocessing.Process(target=run_webview)
    webview_process.start()
    # 逆序清除进程
    webview_process.join()
    flask_process.terminate()
    flask_process.join()
    redis_process.terminate()
    redis_process.join()

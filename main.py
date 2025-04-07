import time

from imports import *
from backend.backMain import run_flask
from frontend.frontMain import run_webview
from database.dataMain import run_database_rides

if __name__ == '__main__':
    multiprocessing.freeze_support()
    redis_process = multiprocessing.Process(target=run_database_rides)
    redis_process.start()
    flask_process = multiprocessing.Process(target=run_flask)
    flask_process.start()
    webview_process = multiprocessing.Process(target=run_webview)
    webview_process.start()
    webview_process.join()
    os.kill(flask_process.pid, signal.SIGTERM)

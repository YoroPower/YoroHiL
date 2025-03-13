from imports import *
from backend.backMain import run_flask
from frontend.frontMain import run_webview

if __name__ == '__main__':
    multiprocessing.freeze_support()
    flask_process = multiprocessing.Process(target=run_flask)
    flask_process.start()
    webview_process = multiprocessing.Process(target=run_webview)
    webview_process.start()
    webview_process.join()
    os.kill(flask_process.pid, signal.SIGTERM)

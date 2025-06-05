# app.py
from imports import *
from backend.routes.api_routes import api_bp, api_test
from backend.routes.socket_events import register_socket_events


def create_app():
    productApp = Flask(__name__, static_folder='../frontend/my-app/out')
    productApp.register_blueprint(api_bp, url_prefix='/api')
    productApp.register_blueprint(api_test, url_prefix='/api/test')
    CORS(productApp, supports_credentials=True)
    return productApp


frontApp = create_app()
socketio = SocketIO(frontApp, cors_allowed_origins="*", async_mode="eventlet")

# 注册Socket.IO事件
register_socket_events(socketio)


@frontApp.route('/')
def index():
    return send_from_directory(frontApp.static_folder, 'index.html')


@frontApp.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(frontApp.static_folder, path)

def run_socketio():
    # socketio.run(frontApp, host='localhost', port=os.getenv("MAIN_PORT", 12233))
    socketio.run(frontApp, host='localhost', port=os.getenv("MAIN_PORT", 12233), use_reloader=False)

def run_flask(event_dict):
    socketio_process = multiprocessing.Process(target=run_socketio)
    socketio_process.start()

    while True:
        if event_dict["flask_exit"].is_set():
            break
        time.sleep(1)

    # 自清理
    socketio_process.terminate()
    socketio_process.join(timeout=10)
    if socketio_process.exitcode is None:
        socketio_process.kill()


if __name__ == '__main__':
    manager = multiprocessing.Manager()
    event_main = manager.dict()
    flask_process = multiprocessing.Process(target=run_flask, args=(event_main,))
    flask_process.start()
    print('\n backMain start')
    flask_process.join()

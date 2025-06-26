# app.py
from imports import *
from backend.routes.api_routes import api_bp, api_test
from backend.routes.socket_events import register_socket_events
from backend.clients.freeMaster_client import freeMaster_client


def GetPath():
    # 动态获取当前.exe所在的目录，确保能正确加载资源文件
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe文件运行，'frozen' 属性会被设置
        app_dir = sys._MEIPASS
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录
    return app_dir

def create_app():
    productApp = Flask(__name__, static_folder='../frontend/my-app/out')
    productApp.register_blueprint(api_bp, url_prefix='/api')
    productApp.register_blueprint(api_test, url_prefix='/test')
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


# 启动fmlite服务器
def start_fmlite_server() -> subprocess.Popen:
    fmlite_server_path = os.path.join(GetPath(), "fmlite", "fmlite.exe")

    args = [
        '--no-open_path',
        '-b yoro master'
    ]

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # 隐藏窗口
    startupinfo.wShowWindow = subprocess.SW_HIDE  # 窗口不可见

    return subprocess.Popen([fmlite_server_path] + args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            startupinfo=startupinfo,  # 应用窗口配置
                            creationflags=subprocess.CREATE_NO_WINDOW)

def run_socketio():
    # socketio.run(frontApp, host='localhost', port=os.getenv("MAIN_PORT", 12233))
    socketio.run(frontApp, host='127.0.0.1', port=os.getenv("MAIN_PORT", 12233), use_reloader=False)

def run_flask(event_dict):
    fmlite_subprocess = None
    if not freeMaster_client.connect():
        fmlite_subprocess = start_fmlite_server()

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
    if fmlite_subprocess is not None:
        fmlite_subprocess.terminate()  # 终止fmlite进程,此处没有强制逻辑，实在无法关闭那么下次调用同一个fmlite进程
        fmlite_subprocess.wait(timeout=10)  # 等待进程终止


if __name__ == '__main__':
    manager = multiprocessing.Manager()
    event_main = manager.dict()
    event_main["flask_exit"] = manager.Event()
    flask_process = multiprocessing.Process(target=run_flask, args=(event_main,))
    flask_process.start()
    print('\n backMain start')
    quit = True
    while quit:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            quit = False
    event_main["flask_exit"].set()
    flask_process.join()

# app.py
from imports import *
from backend.routes.api_routes import api_bp, api_test
from backend.routes.socket_events import register_socket_events


def create_app():
    app = Flask(__name__, static_folder='../frontend/my-app/out')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(api_test, url_prefix='/api/test')
    CORS(app, supports_credentials=True)
    return app


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


def run_flask():
    socketio.run(frontApp, host='localhost', port=5000)


if __name__ == '__main__':
    flask_process = multiprocessing.Process(target=run_flask)
    flask_process.start()
    print('\nbackMain start')
    flask_process.join()

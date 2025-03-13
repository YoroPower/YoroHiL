from flask_socketio import SocketIO, disconnect
from backend.services import heartbeat_service


def register_socket_events(socketio: SocketIO):
    @socketio.on('connect')
    def handle_connect(*args):
        """
        :param args: 标识身份验证auth信息
        :return: 无意义
        """
        print('Client connected')
        heartbeat_service.start_heartbeat()  # 启动心跳自增
        socketio.start_background_task(_send_heartbeat_data)

    @socketio.on('disconnect')
    def handle_disconnect(*args):
        """
        :param args: 标识断开原因，字符串
        :return: 无意义
        """
        print(f'Client {args} disconnected')

        disconnect()

        # 获取当前所有活跃连接
        active_clients = len(socketio.server.environ)

        if active_clients <= 1:  # 当前断开的是最后一个连接时
            heartbeat_service.stop_heartbeat()

    @socketio.on('message')
    def handle_message(data):  # 无名字符串信息
        print('received message: ' + data)

    @socketio.on('json')
    def handle_json(json):  # 无名json信息
        print('received json: ' + str(json))

    @socketio.on('my event')
    def handle_my_custom_event(json):  # 自定义名称信息
        print('received json: ' + str(json))

    def _send_heartbeat_data():
        while True:
            # 发送 device_update（带自增值）
            socketio.emit('device_update', {'value': heartbeat_service.value})
            # 发送固定值 qaq
            socketio.emit('qaq', {'value': 0})
            socketio.sleep(1)  # 合并为每秒发送两个事件

from imports import *


def GetPath():
    # 动态获取当前.exe所在的目录，确保能正确加载资源文件
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe文件运行，'frozen' 属性会被设置
        app_dir = sys._MEIPASS
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录
    return app_dir


# 启动Redis服务器
def start_redis_server()-> subprocess.Popen:
    # Redis服务器和配置文件的路径
    redis_server_path = os.path.join(GetPath(), "Redis_win32", "redis-server.exe")
    redis_conf_path = os.path.join(GetPath(), "Redis_win32", "redis.windows.conf")

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # 隐藏窗口
    startupinfo.wShowWindow = subprocess.SW_HIDE  # 窗口不可见

    return subprocess.Popen([redis_server_path, redis_conf_path],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,
                     startupinfo=startupinfo,  # 应用窗口配置
                     creationflags=subprocess.CREATE_NO_WINDOW)

# 检查Redis服务器是否启动
def check_redis_server():
    try:
        rDP = redis.Redis(host='127.0.0.1', port=os.getenv("REDIS_PORT", 6379), db=0)
        rDP.ping()  # 尝试发送ping命令
        return True
    except redis.exceptions.ConnectionError:
        return False

def run_database_rides(event_dict):
    redis_subprocess = None
    if not check_redis_server(): # 未启动 redis，进行一次启动
        redis_subprocess = start_redis_server()

    # 等待Redis服务器启动
    while not check_redis_server():
        time.sleep(1)

    while True:
        if event_dict["rides_exit"].is_set():
            break
        time.sleep(1)

    # 自清理
    if redis_subprocess is not None:
        redis_subprocess.terminate()  # 终止Redis进程,此处没有强制逻辑，实在无法关闭那么下次调用同一个Redis进程
        redis_subprocess.wait(timeout=10)  # 等待进程终止


if __name__ == '__main__':
    process = multiprocessing.Process(target=run_database_rides)
    process.start()
    print('\n redis start')
    process.join(timeout=35)  # 设置join超时

    if process.is_alive():
        print("错误: Redis 启动超时，强制终止")
        process.terminate()

    # 连接到Redis服务器
    r = redis.Redis(host='127.0.0.1', port=os.getenv("REDIS_PORT", 6379), db=0)
    while True:
        """ """
        # 设置键值对
        r.set('key1', 'value1')
        # 等待5秒
        time.sleep(5)
        # 显示数据
        data = r.get('key1')
        print(f'Data: {data.decode()}')
        # 更新数据
        r.set('key1', 'new value')
        # 等待5秒
        time.sleep(5)
        # 显示数据
        data = r.get('key1')
        print(f'Data: {data.decode()}')

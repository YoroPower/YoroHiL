# services/heartbeat_service.py
from threading import Lock, Event, Thread
from time import sleep


class HeartbeatService:
    def __init__(self):
        self._heartbeat_value = 0
        self._lock = Lock()
        self._heartbeat_active = Event()  # 心跳控制开关
        self._heartbeat_thread = None

    @property
    def value(self):
        with self._lock:
            return self._heartbeat_value

    @value.setter
    def value(self, new_value):
        with self._lock:
            self._heartbeat_value = new_value

    def increment_value(self):
        with self._lock:
            self._heartbeat_value += 1
            return self._heartbeat_value

    def start_heartbeat(self):
        if not self._heartbeat_active.is_set():
            self._heartbeat_active.set()
            self._heartbeat_thread = Thread(target=self._run_heartbeat)
            self._heartbeat_thread.start()

    def stop_heartbeat(self):
        self._heartbeat_active.clear()
        if self._heartbeat_thread:
            self._heartbeat_thread.join()

    def _run_heartbeat(self):
        while self._heartbeat_active.is_set():
            self.increment_value()
            sleep(1)  # 原始逻辑中的自增间隔


heartbeat_service = HeartbeatService()

"""
单例模式的硬件矩阵数据
"""

from imports import *
from backend.clients.freeMaster_client import freeMaster_client
import serial
import serial.tools.list_ports


class ControlReg:
    def __init__(self):
        self.value = 0  # 初始化32位寄存器值为0

    @property
    def run(self):
        return (self.value >> 0) & 0x1

    @run.setter
    def run(self, val):
        if val:
            self.value |= (1 << 0)  # 设置run位
        else:
            self.value &= ~(1 << 0)  # 清除run位

    @property
    def stop(self):
        return (self.value >> 1) & 0x1

    @stop.setter
    def stop(self, val):
        if val:
            self.value |= (1 << 1)  # 设置stop位
        else:
            self.value &= ~(1 << 1)  # 清除stop位

    @property
    def update(self):
        return (self.value >> 2) & 0x1

    @update.setter
    def update(self, val):
        if val:
            self.value |= (1 << 2)  # 设置update位
        else:
            self.value &= ~(1 << 2)  # 清除update位

    @property
    def model(self):
        return (self.value >> 3) & 0x3  # 获取model的2位

    @model.setter
    def model(self, val):
        if 0 <= val <= 3:  # 确保val在0到3之间
            self.value &= ~(0x3 << 3)  # 清除原有model位
            self.value |= (val << 3)  # 设置新的model位

    @property
    def step(self):
        return (self.value >> 16) & 0x1

    @step.setter
    def step(self, val):
        if val:
            self.value |= (1 << 16)  # 设置step位
        else:
            self.value &= ~(1 << 16)  # 清除step位

    @property
    def monitor(self):
        return (self.value >> 17) & 0x1

    @monitor.setter
    def monitor(self, val):
        if val:
            self.value |= (1 << 17)  # 设置monitor位
        else:
            self.value &= ~(1 << 17)  # 清除monitor位

    @property
    def ioCfg(self):
        return (self.value >> 18) & 0x1

    @ioCfg.setter
    def ioCfg(self, val):
        if val:
            self.value |= (1 << 18)  # 设置ioCfg位
        else:
            self.value &= ~(1 << 18)  # 清除ioCfg位

    @property
    def rangCfg(self):
        return (self.value >> 19) & 0x1

    @rangCfg.setter
    def rangCfg(self, val):
        if val:
            self.value |= (1 << 19)  # 设置ioCfg位
        else:
            self.value &= ~(1 << 19)  # 清除ioCfg位

    def get_value(self):
        return self.value  # 返回当前32位寄存器值

    def set_value(self, value):
        self.value = value & 0xFFFFFFFF  # 确保值为32位

class HardMatrix:
    def __init__(self):
        self.connected = False  # 硬件连接状态
        self.preprocessing = False  # 硬件预处理状态
        self.NewCtrl = ControlReg() # 控制寄存器定义

    def connect(self):
        try:
            self.connected = freeMaster_client.init()
            v = freeMaster_client.read_variable("NewCtrl")
            if (not self.connected) or (v is None):
                return jsonify({"status": "ERR", "reason": "not connected"})
            self.NewCtrl.set_value(v)
        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})

        return jsonify({"status": "OK"})

    def disconnect(self):
        try:
            freeMaster_client.stop()
            self.connected = False
        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})

        return jsonify({"status": "OK"})

    def connectCfg(self, port_name):
        ports = serial.tools.list_ports.comports()
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        if port_name not in available_ports:
            return jsonify({"status": "ERR", "reason": "无效的串口"}), 400
        freeMaster_client.port = port_name
        return jsonify({"status": "OK"})

    def NewCtrlReread(self):
        try:
            v = freeMaster_client.read_variable("NewCtrl")
            self.NewCtrl.set_value(v)
        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})

        return jsonify({"status": "OK"})

    def NewCtrlSimStop(self):
        try:
            self.NewCtrlReread()
            self.NewCtrl.run = False
            self.NewCtrl.stop = True
            freeMaster_client.write_variable("NewCtrl", self.NewCtrl.get_value())
        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})
        return jsonify({"status": "OK"})

    def NewCtrlSimRun(self):
        try:
            self.NewCtrlReread()
            self.NewCtrl.run = True
            self.NewCtrl.stop = False
            freeMaster_client.write_variable("NewCtrl", self.NewCtrl.get_value())
        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})
        return jsonify({"status": "OK"})

    def NewCtrlIOCfg(self):
        try:
            self.NewCtrlReread()
            self.NewCtrl.ioCfg = True
            freeMaster_client.write_variable("NewCtrl", self.NewCtrl.get_value())
        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})
        return jsonify({"status": "OK"})

    def NewCtrlRangCfg(self):
        try:
            self.NewCtrlReread()
            self.NewCtrl.rangCfg = True
            freeMaster_client.write_variable("NewCtrl", self.NewCtrl.get_value())
        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})
        return jsonify({"status": "OK"})

obj_HardMatrix = HardMatrix()
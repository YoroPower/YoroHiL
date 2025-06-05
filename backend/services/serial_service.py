import serial
import numpy as np
from flask import jsonify

import serial.tools.list_ports

# 获取所有串口设备列表
ports = serial.tools.list_ports.comports()

# 判断列表是否非空，避免 IndexError
if ports:
    # 直接访问第一个设备的 description 属性
    COM_PORT = ports[0].description
else:
    COM_PORT = None

BAUD_RATE = 115200  # 波特率


def setComPort(port_name):
    global COM_PORT
    global BAUD_RATE

    available_ports = [port.device for port in serial.tools.list_ports.comports()]
    if port_name not in available_ports:
        return jsonify({"status": "ERR", "reason": "无效的串口"}), 400

    try:
        COM_PORT = port_name
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    except Exception as e:
        return jsonify({"status": "ERR", "reason": str(e)})

    return jsonify({"status": "OK"})

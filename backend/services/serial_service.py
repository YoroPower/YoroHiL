import serial
import numpy as np
from flask import jsonify

from backend.protocol.inLoop import MatrixSender
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


def send_topology_data(data):
    topology_value = int(data)

    # 配置串口参数

    attrU = 1
    attrL = 2
    attrC = 3
    attrR = 4

    # 发送拓扑数据到下位机
    data_dict = {
        1: {  # 0-10V-100mH-10uF-0
            1: {
                "A": np.array([[1, -1, 0], [0, 1, -1]], dtype=np.int8),
                "G_inv": np.array([[9.9999999e-04, 9.9999899e-10],
                                   [9.9999899e-10, 9.9999900e-02]]),
                "YL": np.array([[0.e+00], [1.e-05], [0.e+00]]),
                "YC": np.array([[0.e+00], [0.e+00], [10.e+00]]),
                "YR": np.array([[1000.e+00], [0.e+00], [0.e+00]]),
                "J": np.array([[10000.], [0.], [0.]]),
                "attr": np.array([[attrU], [attrL], [attrC]]),
                "dt": 1e-6,
            },
        },
        2: {  # 0-10V-100mH-10uF=100Ω-0
            1: {
                "A": np.array([[1, -1, 0, 0], [0, 1, -1, -1]], dtype=np.int8),
                "G_inv": np.array([[9.99999990e-04, 9.98999991e-10],
                                   [9.98999991e-10, 9.99000001e-02]]),
                "YL": np.array([[0.e+00], [1.e-05], [0.e+00], [0.e+00]]),
                "YC": np.array([[0.e+00], [0.e+00], [0.e+00], [10.e+00]]),
                "YR": np.array([[1000.e+00], [0.e+00], [1.e-2], [0.e+00]]),
                "J": np.array([[10000.], [0.], [0.], [0.]]),
                "attr": np.array([[attrU], [attrL], [attrR], [attrC]]),
                "dt": 1e-6,
            },
        }
    }

    try:
        sender = MatrixSender(matrix_id=0)
        # 协议命令映射表（字段名: 生成函数）
        packet_map = {
            "A": sender.send_A,
            "G_inv": sender.send_G_inv,
            "YL": sender.send_YL,
            "YC": sender.send_YC,
            "YR": sender.send_YR,
            "J": sender.send_J,
            "attr": sender.send_attr
        }
        # 构造发送数据包队列
        packets = []

        # 发送id指定
        packets.append(sender.send_matrix_id())

        # 1. 清除矩阵
        packets.append(sender.send_clear())

        # 2. 发送当前拓扑所有配置数据
        topology_data = data_dict[topology_value][1]
        for key, func in packet_map.items():
            if key in topology_data:
                packets.append(func(topology_data[key]))

        # 3. 启动仿真（启动matrix_id=1）
        packets.append(sender.send_start())

        # 串口数据发送
        with serial.Serial(COM_PORT, BAUD_RATE, timeout=1) as ser:
            ser.write(b''.join(packets))

        # except KeyError as e:
        #     print(f"无效拓扑配置: {str(e)}")
        # except ValueError as e:
        #     print(f"数据验证失败: {str(e)}")
        # except serial.SerialException as e:
        #     print(f"串口通信失败: {str(e)}")
        # except Exception as e:
        #     print(f"未知错误: {str(e)}")
    except Exception as e:
        return jsonify({"status": "ERR", "reason": str(e)}), 400

    return jsonify({"status": "OK"})


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

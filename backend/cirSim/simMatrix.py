"""
单例模式的电路数据
"""

from imports import *
from backend.algorithm import psimXML, pspiceNET


class SimMatrix:

    def __init__(self):
        self.observable_data = None  # 可观测数据列表
        self.accList = None  # 支路列表
        self.attr = None  # 支路属性列表
        self.A = None # 支路-节点矩阵
        self.n_igbt = None # 可控器件数量
        self.YR = None # 电阻导纳矩阵
        self.YL = None # 电感导纳矩阵
        self.YC = None # 电容导纳矩阵
        self.J = None # 历史电流源初值

        self.G_inv_R = None  # R模拟策略下导纳矩阵的逆
        self.G_inv_LC = None # LC模拟策略下导纳矩阵的逆

        self.dt = 1e-6 # 仿真步长
        self.xml_file_path = None # 已选择的xml文件路径
        self.net_file_path = None  # 已选择的net文件路径

    def loadXML(self, xml_file_path):
        try:
            self.observable_data, self.accList, self.attr, self.A, self.n_igbt, self.G_inv_R, self.G_inv_LC, self.YR, self.YL, self.YC, self.J = psimXML(self.dt, xml_file_path)
            self.xml_file_path = xml_file_path

        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})

        return jsonify({"status": "OK"})

    def loadNET(self, net_file_path):
        try:
            self.observable_data, self.accList, self.attr, self.A, self.n_igbt, self.G_inv_R, self.G_inv_LC, self.YR, self.YL, self.YC, self.J = pspiceNET(self.dt, net_file_path)
            self.net_file_path = net_file_path

        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})

        return jsonify({"status": "OK"})


obj_SimMatrix = SimMatrix()

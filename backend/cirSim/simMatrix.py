"""
单例模式的电路数据
"""

from imports import *
from backend.algorithm import psimXML, pspiceNET

class MatrixData:
    def __init__(self):
        self.observable_data = None  # 可观测数据列表
        self.accList = None  # 支路列表
        self.attr = None  # 支路属性列表
        self.A = None  # 支路-节点矩阵
        self.n_igbt = None  # 可控器件数量
        self.YR = None  # 电阻导纳矩阵
        self.YL = None  # 电感导纳矩阵
        self.YC = None  # 电容导纳矩阵
        self.J = None  # 历史电流源初值

        self.G_inv_R = None  # R模拟策略下导纳矩阵的逆
        self.G_inv_LC = None  # LC模拟策略下导纳矩阵的逆

        self.file_path = None  # 已选择的文件路径

class SimMatrix:

    def __init__(self):
        self.XMLData = MatrixData()
        self.NETData = MatrixData()

        self.dt = 1e-6 # 仿真步长

        self.SimType = 0 # 0 XML 1 NET

    def loadXML(self, xml_file_path):
        try:
            (self.XMLData.observable_data,
             self.XMLData.accList,
             self.XMLData.attr,
             self.XMLData.A,
             self.XMLData.n_igbt,
             self.XMLData.G_inv_R,
             self.XMLData.G_inv_LC,
             self.XMLData.YR,
             self.XMLData.YL,
             self.XMLData.YC,
             self.XMLData.J) = psimXML(self.dt, xml_file_path)
            self.XMLData.file_path = xml_file_path

        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})

        return jsonify({"status": "OK"})

    def loadNET(self, net_file_path):
        try:
            (self.NETData.observable_data,
             self.NETData.accList,
             self.NETData.attr,
             self.NETData.A,
             self.NETData.n_igbt,
             self.NETData.G_inv_R,
             self.NETData.G_inv_LC,
             self.NETData.YR,
             self.NETData.YL,
             self.NETData.YC,
             self.NETData.J) = pspiceNET(self.dt, net_file_path)
            self.NETData.file_path = net_file_path

        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})

        return jsonify({"status": "OK"})

    def setType(self, type:int):
        self.SimType = type


obj_SimMatrix = SimMatrix()

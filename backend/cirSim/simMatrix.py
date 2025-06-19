"""
单例模式的电路数据
"""

from imports import *
import websockets
from backend.algorithm import psimXML, pspiceNET
from backend.algorithm import attrU, attrR, attrL, attrC, attrIP, attrIGBT, attrDiode, attrI
from backend.clients.freeMaster_client import freeMaster_client
from backend.cirSim.hardMatrix import  obj_HardMatrix


class MatrixData:
    def __init__(self):
        self.observable_data = None  # 可观测数据列表
        self.accList = None  # 支路列表
        self.attrName = None  # 支路器件名称列表
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

        self.SimType = 0 # 0 XML 1 NET 2 预设电路

    def loadXML(self, xml_file_path):
        try:
            (self.XMLData.observable_data,
             self.XMLData.accList,
             self.XMLData.attrName,
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
             self.NETData.attrName,
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

    def setType(self, stype:int):
        self.SimType = stype

    def simPreprocess(self):
        data = self.XMLData
        if self.SimType == 0:
            data = self.XMLData
        elif self.SimType == 1:
            data = self.NETData

        if freeMaster_client.ws is None or freeMaster_client.ws.close:
            return jsonify({"status": "ERR", "reason": "freemaster未连接"}), 400

        return jsonify({"status": "OK"})

    def simOpen(self):
        if freeMaster_client.ws is None or freeMaster_client.ws.state != websockets.protocol.State.OPEN:
            return jsonify({"status": "ERR", "reason": "freemaster未连接"}), 400

        data = self.XMLData
        if self.SimType == 0:
            data = self.XMLData
        elif self.SimType == 1:
            data = self.NETData
        elif self.SimType == 2:
            data = MatrixData() # 预设新构建

        if data.file_path is None:
            return jsonify({"status": "ERR", "reason": "接线表未选择"}), 400

        try:
            obj_HardMatrix.NewCtrlReread()
            obj_HardMatrix.NewCtrlSimStop()
            """一些不需要预采集信息的debug(专供psim) 矩阵下载耗时，后续改造为开线程异步 呃，或许本来就是异步的，待测试"""
            if self.SimType == 0:
                for index, (key, matrix) in enumerate(data.G_inv_R.items()):
                    pp_R = (matrix @ data.A).T @ data.A
                    for i in range(pp_R.shape[0]):  # 行数
                        for j in range(pp_R.shape[1]):  # 列数
                            freeMaster_client.write_variable(f"SysMatrixRun.pp_R[{index}][{i}][{j}]", pp_R[i][j])

                n = min(len(data.YL), len(data.YL[0]))
                for index in range(n):
                    value = data.YL[index][index]
                    freeMaster_client.write_variable(f"SysMatrixRun.YL[{index}]", value)

                n = min(len(data.YC), len(data.YC[0]))
                for index in range(n):
                    value = data.YC[index][index]
                    freeMaster_client.write_variable(f"SysMatrixRun.YC[{index}]", value)

                for index, value in enumerate(data.attr):
                    freeMaster_client.write_variable(f"SysMatrixRun.attr[{index}]", value)

                for index, value in enumerate(data.J):
                    freeMaster_client.write_variable(f"SysMatrixRun.J[{index}]", value)

                numTemp_L = 0
                numTemp_C = 0
                numTemp_igbt = 0
                numTemp_diode = 0
                L_indices = []
                C_indices = []
                igbt_indices = []
                diode_indices = []
                comb_map_key = []
                comb_map_value = []

                # 提取矩阵信息
                for i in range( len(data.attr)):
                    if data.attr[i] == attrL:
                        L_indices.append(i)
                        numTemp_L += 1
                    elif data.attr[i] == attrC:
                        C_indices.append(i)
                        numTemp_C += 1
                    elif data.attr[i] == attrIGBT:
                        igbt_indices.append(i)
                        numTemp_igbt += 1
                    elif data.attr[i] == attrDiode:
                        diode_indices.append(i)
                        numTemp_diode += 1
                for index in range(len(L_indices)):
                    freeMaster_client.write_variable(f"MatrixHandle.L_indices[{index}]", L_indices[index])
                for index in range(len(C_indices)):
                    freeMaster_client.write_variable(f"MatrixHandle.C_indices[{index}]", C_indices[index])
                for index in range(len(igbt_indices)):
                    freeMaster_client.write_variable(f"MatrixHandle.igbt_indices[{index}]", igbt_indices[index])
                for index in range(len(diode_indices)):
                    freeMaster_client.write_variable(f"MatrixHandle.diode_indices[{index}]", diode_indices[index])

                # 更新计数
                freeMaster_client.write_variable("MatrixHandle.L_num", numTemp_L)
                freeMaster_client.write_variable("MatrixHandle.C_num", numTemp_C)
                freeMaster_client.write_variable("MatrixHandle.igbt_num", numTemp_igbt)
                freeMaster_client.write_variable("MatrixHandle.diode_num", numTemp_diode)

                # R组合映射
                numTemp_comb = 0
                d_comb = 1 << numTemp_diode  # 2 ** numTemp_diode
                i_comb = 1 << numTemp_igbt  # 2 ** numTemp_igbt

                for i in range(i_comb):
                    for j in range(d_comb):
                        comb_map_key.append((j << 20) | i)
                        comb_map_value.append(numTemp_comb)
                        numTemp_comb += 1

                for i in range(numTemp_comb):
                    freeMaster_client.write_variable(f"MatrixHandle.comb_map_key[{i}]", comb_map_key[i])
                    freeMaster_client.write_variable(f"MatrixHandle.comb_map_value[{i}]", comb_map_value[i])

                freeMaster_client.write_variable(f"MatrixHandle.comb_num", numTemp_comb)


                obj_HardMatrix.NewCtrlSimRun()
            """"""

        except Exception as e:
            return jsonify({"status": "ERR", "reason": str(e)})

        return jsonify({"status": "OK"})



obj_SimMatrix = SimMatrix()

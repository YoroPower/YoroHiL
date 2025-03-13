from imports import *


class SimMatrix:

    def __init__(self):
        self.elmList = None  # 器件列表
        self.rightSide = [0.0 for _ in range(5)]
        self.matrix = [[0.0 for _ in range(5)] for _ in range(5)]  # 实际矩阵
        self.typeHandlers = {
            "Resistor": self.resistor_handler,
            "Voltage": self.voltage_handler,
            "Wire": self.wire_handler
        }
        self.voltage_source_list = ["Voltage", "Wire"]
        self.errCode = {
            0: '正确返回',
            101: '矩阵构建失败',
            301: 'type不在可处理范围',
        }

    def set(self, components: list):
        # 寄存器件列表
        self.elmList = components
        # 重新定义矩阵大小
        sn = 0
        for component in components:
            component_type = component.get('type')
            if component_type in self.voltage_source_list:
                component['voltSource'] = sn
                sn += 1
        newLen = len(components) - 1 + sn
        self.matrix = [[0.0 for _ in range(newLen)] for _ in range(newLen)]
        self.rightSide = [0.0 for _ in range(newLen)]
        # 触发各器件构造
        for component in components:
            component_type = component.get('type')
            state = 0
            if component_type in self.typeHandlers:
                handler = self.typeHandlers[component_type]
                state = handler(component)
            else:
                return 301
            if state != 0:
                return state

    def resistor_handler(self, device: dict):
        print(f"type = {device['type']}")
        r0 = 1 / device['value']
        self._stamp_matrix(device['node']['1'], device['node']['1'], device['value'])
        self._stamp_matrix(device['node']['2'], device['node']['2'], device['value'])
        self._stamp_matrix(device['node']['1'], device['node']['2'], -device['value'])
        self._stamp_matrix(device['node']['2'], device['node']['1'], -device['value'])
        return 0

    def voltage_handler(self, device: dict):
        print(f"type = {device['type']}")
        self._stamp_matrix(len(self.elmList) + device['voltSource'], device['node']['1'], -1)
        self._stamp_matrix(len(self.elmList) + device['voltSource'], device['node']['2'], 1)
        self._stamp_rightSide(len(self.elmList) + device['voltSource'], device['value'])
        self._stamp_matrix(device['node']['1'], len(self.elmList) + device['voltSource'], -1)
        self._stamp_matrix(device['node']['2'], len(self.elmList) + device['voltSource'], 1)
        return 0

    def wire_handler(self, device: dict):
        print(f"type = {device['type']}")
        self._stamp_matrix(len(self.elmList) + device['voltSource'], device['node']['1'], -1)
        self._stamp_matrix(len(self.elmList) + device['voltSource'], device['node']['2'], 1)
        self._stamp_rightSide(len(self.elmList) + device['voltSource'], 0)
        self._stamp_matrix(device['node']['1'], len(self.elmList) + device['voltSource'], -1)
        self._stamp_matrix(device['node']['2'], len(self.elmList) + device['voltSource'], 1)
        return 0

    def _stamp_matrix(self, i, j, x):
        if i < 0 and j < 0:
            return
        i -= 1
        j -= 1
        self.matrix[i][j] += x

    def _stamp_rightSide(self, i, x):
        if i < 0:
            return
        i -= 1
        self.rightSide[i] += x


obj_SimMatrix = SimMatrix()

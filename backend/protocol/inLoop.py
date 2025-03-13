import struct
import numpy as np
from typing import Union


class MatrixSender:
    """
    矩阵协议发送器（支持多矩阵编号）
    功能方法对照表：
    +---------------------+-----------------------+
    | 方法名              | 对应功能              |
    +---------------------+-----------------------+
    | send_clear          | 清除矩阵（0x0000 01）|
    | send_start          | 启动仿真（0x0000 02）|
    | send_stop           | 停止仿真（0x0000 03）|
    | send_A              | 发送导纳矩阵A        |
    | send_G_inv          | 发送导纳逆矩阵G_inv  |
    | send_J              | 发送历史电流源J      |
    | send_attr           | 发送属性矩阵attr     |
    | send_YL             | 发送支路L导纳        |
    | send_YC             | 发送支路C导纳        |
    | send_YR             | 发送支路R导纳        |
    +---------------------+-----------------------+
    """

    def __init__(self, matrix_id: int = 0):
        self.matrix_id = matrix_id

    def _calc_checksum(self, data: bytes) -> int:
        """带进位累加的校验和计算"""
        checksum = 0
        for byte in data:
            checksum += byte
            if checksum > 0xFFFF:
                checksum = (checksum & 0xFFFF) + 1
        return checksum

    def _build_header(self, cmd: int, ext_info: int, data_len: int) -> bytes:
        """构建协议头（大端序）"""
        return struct.pack('>HHH', cmd, ext_info, data_len + 2)  # +2 for checksum

    def send_clear(self) -> bytes:
        """清除矩阵（CMD 0x0000 操作码0x01）"""
        cmd = 0x0000
        ext_info = 0x01
        data = struct.pack('>H', 0x5555)
        header = self._build_header(cmd, ext_info, len(data))
        checksum = self._calc_checksum(header + data)
        return header + data + struct.pack('>H', checksum)

    def send_start(self) -> bytes:
        """启动仿真（CMD 0x0000 操作码0x02）"""
        cmd = 0x0000
        ext_info = 0x02
        data = struct.pack('>H', 0x5555)
        header = self._build_header(cmd, ext_info, len(data))
        checksum = self._calc_checksum(header + data)
        return header + data + struct.pack('>H', checksum)

    def send_matrix_id(self) -> bytes:
        """启动仿真（CMD 0x0000 操作码0x10）"""
        cmd = 0x0000
        ext_info = 0x10
        data = struct.pack('>I', self.matrix_id)  # 大端序 4 字节无符号整型
        header = self._build_header(cmd, ext_info, len(data))
        checksum = self._calc_checksum(header + data)
        return header + data + struct.pack('>H', checksum)

    def send_matrix(self, cmd: int, matrix: np.ndarray,
                    shape_validator: callable, data_packer: callable) -> bytes:
        """通用矩阵发送方法"""
        matrix = np.asarray(matrix)
        shape_validator(matrix)  # 验证矩阵形状

        # 构造拓展信息
        if cmd == 0x0001:  # A矩阵特殊处理（列数）
            cols = matrix.shape[1]
            ext_info = cols
        else:
            dim = matrix.shape[0] if cmd in [0x0003, 0x0005, 0x0006, 0x0007] else matrix.shape[1]
            ext_info = (dim & 0xFF)

        # 数据打包
        data = data_packer(matrix)

        # 构造协议
        header = self._build_header(cmd, ext_info, len(data))
        checksum = self._calc_checksum(header + data)
        return header + data + struct.pack('>H', checksum)

    # 以下是各矩阵的专用发送方法
    def send_A(self, matrix: np.ndarray) -> bytes:
        def validator(m):
            if m.ndim != 2 or m.dtype != np.int8:
                raise ValueError("A矩阵必须为int8类型的二维数组")

        return self.send_matrix(0x0001, matrix, validator,
                                lambda m: b''.join(struct.pack('b', v) for v in m.flatten()))

    def send_G_inv(self, matrix: np.ndarray) -> bytes:
        def validator(m):
            if m.ndim != 2 or m.shape[0] != m.shape[1]:
                raise ValueError("G_inv必须为方阵")
            if m.shape[0] > 0xFF:
                raise ValueError("矩阵维度超过255限制")

        return self.send_matrix(0x0002, matrix, validator,
                                lambda m: b''.join(struct.pack('<f', v) for v in m.flatten()))

    def send_J(self, matrix: np.ndarray) -> bytes:
        def validator(m):
            if m.ndim != 2 or m.shape[1] != 1:
                raise ValueError("J必须为单列向量")

        return self.send_matrix(0x0003, matrix, validator,
                                lambda m: b''.join(struct.pack('<f', v) for v in m.flatten()))

    def send_attr(self, matrix: np.ndarray) -> bytes:
        def validator(m):
            if m.ndim != 2 or m.shape[1] != 1:
                raise ValueError("attr必须为单列向量")

        return self.send_matrix(0x0004, matrix, validator,
                                lambda m: b''.join(struct.pack('<f', v) for v in m.flatten()))

    def send_YL(self, matrix: np.ndarray) -> bytes:
        def validator(m):
            if m.ndim != 2 or m.shape[1] != 1:
                raise ValueError("YL必须为单列向量")

        return self.send_matrix(0x0005, matrix, validator,
                                lambda m: b''.join(struct.pack('<f', v) for v in m.flatten()))

    def send_YC(self, matrix: np.ndarray) -> bytes:
        def validator(m):
            if m.ndim != 2 or m.shape[1] != 1:
                raise ValueError("YC必须为单列向量")

        return self.send_matrix(0x0006, matrix, validator,
                                lambda m: b''.join(struct.pack('<f', v) for v in m.flatten()))

    def send_YR(self, matrix: np.ndarray) -> bytes:
        def validator(m):
            if m.ndim != 2 or m.shape[1] != 1:
                raise ValueError("YR必须为单列向量")

        return self.send_matrix(0x0007, matrix, validator,
                                lambda m: b''.join(struct.pack('<f', v) for v in m.flatten()))

import struct
import numpy as np
from typing import Union


def clearMatrix(matrix_id: int = 0) -> bytes:
    """
    清除原矩阵（CMD=0x0000  operation_code = 0x01）
    协议格式：
    固定头 00 00 | 拓展信息[保留|操作码] | 长度 | 数据 0x5555 | 校验和
    参数约定：
    - 拓展信息高字节保留，低字节=操作码(0x01表清除)
    - 数据段固定为0x5555
    """
    # 协议字段初始化
    cmd = 0x0000
    operation_code = 0x01  # 清除操作
    ext_info = (matrix_id << 8) | (operation_code & 0xFF)  # 兼容矩阵编号占位
    msg_content = 0x5555

    # 数据段打包（大端序）
    data_bytes = struct.pack('>H', msg_content)

    # 长度计算（数据长度 + 校验和字段）
    length = len(data_bytes) + 2  # 2字节校验和

    # 协议头构造（>HHH表示3个unsigned short大端序）
    header_bytes = struct.pack('>HHH', cmd, ext_info, length)

    # 校验和计算（带进位累加）
    checksum = 0
    for byte in header_bytes + data_bytes:  # 遍历所有协议字段
        checksum += byte
        if checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + 1

    # 完整报文组装
    return header_bytes + data_bytes + struct.pack('>H', checksum)


def openMatrix(matrix_id: int = 0) -> bytes:
    """
    启动矩阵仿真（CMD=0x0000  operation_code = 0x02）
    协议格式：
    固定头 00 00 | 拓展信息[保留|操作码] | 长度 | 数据 0x5555 | 校验和
    参数约定：
    - 拓展信息高字节保留，低字节=操作码(0x02表启动)
    - 数据段固定为0x5555
    """
    # 协议字段初始化
    cmd = 0x0000
    operation_code = 0x02  # 启动操作
    ext_info = (matrix_id << 8) | (operation_code & 0xFF)  # 兼容矩阵编号占位
    msg_content = 0x5555

    # 数据段打包（大端序）
    data_bytes = struct.pack('>H', msg_content)

    # 长度计算（数据长度 + 校验和字段）
    length = len(data_bytes) + 2  # 2字节校验和

    # 协议头构造（>HHH表示3个unsigned short大端序）
    header_bytes = struct.pack('>HHH', cmd, ext_info, length)

    # 校验和计算（带进位累加）
    checksum = 0
    for byte in header_bytes + data_bytes:  # 遍历所有协议字段
        checksum += byte
        if checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + 1

    # 完整报文组装
    return header_bytes + data_bytes + struct.pack('>H', checksum)


def stopMatrix(matrix_id: int = 0) -> bytes:
    """
    启动矩阵仿真（CMD=0x0000  operation_code = 0x03）
    协议格式：
    固定头 00 00 | 拓展信息[保留|操作码] | 长度 | 数据 0x5555 | 校验和
    参数约定：
    - 拓展信息高字节保留，低字节=操作码(0x03表停止)
    - 数据段固定为0x5555
    """
    # 协议字段初始化
    cmd = 0x0000
    operation_code = 0x02  # 启动操作
    ext_info = (matrix_id << 8) | (operation_code & 0xFF)  # 兼容矩阵编号占位
    msg_content = 0x5555

    # 数据段打包（大端序）
    data_bytes = struct.pack('>H', msg_content)

    # 长度计算（数据长度 + 校验和字段）
    length = len(data_bytes) + 2  # 2字节校验和

    # 协议头构造（>HHH表示3个unsigned short大端序）
    header_bytes = struct.pack('>HHH', cmd, ext_info, length)

    # 校验和计算（带进位累加）
    checksum = 0
    for byte in header_bytes + data_bytes:  # 遍历所有协议字段
        checksum += byte
        if checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + 1

    # 完整报文组装
    return header_bytes + data_bytes + struct.pack('>H', checksum)


def set_A(matrix: Union[np.ndarray, list], matrix_id: int = 0) -> bytes:
    """
    发送节点导纳矩阵A（CMD=0x0001）
    协议格式：
    固定头 00 01 | 拓展信息 拓扑编号 列数 | 长度 | 数据 | 校验和
    """
    # 协议头构造
    cmd = 0x0001  # 固定指令头
    cols = matrix.shape[1]  # 列数
    ext_info = (matrix_id << 8) | cols  # 高字节为矩阵编号，低字节为列数

    # 数据打包（单字节小端序）
    data_bytes = b''.join(struct.pack('b', val) for val in matrix.flatten())

    # 协议字段构造
    length = len(data_bytes) + 2  # 数据长度 + 校验和长度
    header_bytes = struct.pack('>HHH', cmd, ext_info, length)

    # 校验和计算（带进位循环）
    checksum = 0
    for byte in header_bytes + data_bytes:
        checksum += byte
        if checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + 1  # 处理进位

    # 完整数据包
    return header_bytes + data_bytes + struct.pack('>H', checksum)


def set_G_inv(matrix: Union[np.ndarray, list], matrix_id: int = 0) -> bytes:
    """
    发送导纳逆矩阵G_inv（CMD=0x0002）
    协议格式：
    固定头 00 02 | 拓展信息[矩阵编号|行列数] | 长度 | 数据 | 校验和
    参数约束：
    - 必须为正方形矩阵（N x N）
    - 元素为单精度浮点数
    - 矩阵维度范围1-255（用8bit编码）
    """
    # 参数校验
    matrix = np.asarray(matrix, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("必须为正方形矩阵")
    n = matrix.shape[1]
    if not (1 <= n <= 0xFF):
        raise ValueError("矩阵维度需在1-255之间")

    # 协议头构造
    cmd = 0x0002
    # 拓展信息编码：高字节=矩阵编号，低字节= 列数
    ext_info = (matrix_id << 8) | (n & 0xFF)

    # 数据打包（小端浮点）
    data_bytes = b''.join(struct.pack('<f', val) for val in matrix.flatten())

    # 协议字段构造
    length = len(data_bytes) + 2  # 数据长度 + 校验和
    header_bytes = struct.pack('>HHH', cmd, ext_info, length)

    # 校验和计算（带进位循环）
    checksum = 0
    for byte in header_bytes + data_bytes:
        checksum += byte
        if checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + 1

    return header_bytes + data_bytes + struct.pack('>H', checksum)


def set_J(matrix: Union[np.ndarray, list], matrix_id: int = 0) -> bytes:
    """
    发送历史电流源初始值J（CMD=0x0003）
    协议格式：
    固定头 00 03 | 拓展信息[矩阵编号|行数] | 长度 | 数据 | 校验和
    参数约束：
    - 必须为单列向量（N x 1）
    - 元素为单精度浮点数
    - 矩阵行数范围1-255（用8bit编码）
    """
    # 参数校验
    matrix = np.asarray(matrix, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[1] != 1:
        raise ValueError("必须为单列向量（N x 1）")
    n = matrix.shape[0]
    if not (1 <= n <= 255):
        raise ValueError("矩阵行数需在1-15之间")

    # 协议头构造
    cmd = 0x0003
    # 拓展信息编码：高字节=矩阵编号，低字节=行数
    ext_info = (matrix_id << 8) | (n & 0xFF)

    # 数据打包（小端浮点）
    data_bytes = b''.join(struct.pack('<f', val) for val in matrix.flatten())

    # 协议字段构造
    length = len(data_bytes) + 2  # 数据长度 + 校验和
    header_bytes = struct.pack('>HHH', cmd, ext_info, length)

    # 校验和计算（带进位循环）
    checksum = 0
    for byte in header_bytes + data_bytes:
        checksum += byte
        if checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + 1

    return header_bytes + data_bytes + struct.pack('>H', checksum)


def set_attr(matrix: Union[np.ndarray, list], matrix_id: int = 0) -> bytes:
    """
    发送属性矩阵attr（CMD=0x0004）
    协议格式：
    固定头 00 04 | 拓展信息[矩阵编号|列数] | 长度 | 数据 | 校验和
    参数约束：
    - 必须为单行向量（1 x N）
    - 元素为单精度浮点数
    - 矩阵列数范围1-255（用8bit编码）
    """
    # 参数校验
    matrix = np.asarray(matrix, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[0] != 1:
        raise ValueError("必须为单行向量（1 x N）")
    n = matrix.shape[1]
    if not (1 <= n <= 255):
        raise ValueError("矩阵列数需在1-255之间")

    # 协议头构造
    cmd = 0x0004
    # 拓展信息编码：高字节=矩阵编号，低字节=列数
    ext_info = (matrix_id << 8) | (n & 0xFF)

    # 数据打包（小端浮点）
    data_bytes = b''.join(struct.pack('<f', val) for val in matrix.flatten())

    # 协议字段构造
    length = len(data_bytes) + 2  # 数据长度 + 校验和
    header_bytes = struct.pack('>HHH', cmd, ext_info, length)

    # 校验和计算（带进位循环）
    checksum = 0
    for byte in header_bytes + data_bytes:
        checksum += byte
        if checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + 1

    return header_bytes + data_bytes + struct.pack('>H', checksum)


def set_YL(matrix: Union[np.ndarray, list], matrix_id: int = 0) -> bytes:
    """
    发送支路L导纳向量YL（CMD=0x0005）
    协议格式：
    固定头 00 05 | 拓展信息[矩阵编号|行数] | 长度 | 数据 | 校验和
    参数约束：
    - 必须为单列向量（N x 1）
    - 元素为单精度浮点数
    - 矩阵行数范围1-255（用8bit编码）
    """
    # 参数校验
    matrix = np.asarray(matrix, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[1] != 1:  # 校验列数必须为1
        raise ValueError("必须为单列向量（N x 1）")
    n = matrix.shape[0]  # 获取行数
    if not (1 <= n <= 255):
        raise ValueError("矩阵行数需在1-255之间")

    # 协议头构造
    cmd = 0x0005  # 修改命令码
    # 拓展信息编码：高字节=矩阵编号，低字节=行数
    ext_info = (matrix_id << 8) | (n & 0xFF)

    # 数据打包（保持小端浮点格式）
    data_bytes = b''.join(struct.pack('<f', val) for val in matrix.flatten())

    # 协议字段构造（结构相同）
    length = len(data_bytes) + 2  # 数据长度 + 校验和
    header_bytes = struct.pack('>HHH', cmd, ext_info, length)

    # 校验和计算（算法相同）
    checksum = 0
    for byte in header_bytes + data_bytes:
        checksum += byte
        if checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + 1

    return header_bytes + data_bytes + struct.pack('>H', checksum)


def set_YC(matrix: Union[np.ndarray, list], matrix_id: int = 0) -> bytes:
    """
    发送支路C导纳向量Yc（CMD=0x0006）
    协议格式：
    固定头 00 06 | 拓展信息[矩阵编号|行数] | 长度 | 数据 | 校验和
    参数约束：
    - 必须为单列向量（N x 1）
    - 元素为单精度浮点数
    - 矩阵行数范围1-255（用8bit编码）
    """
    # 参数校验
    matrix = np.asarray(matrix, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[1] != 1:  # 校验列数必须为1
        raise ValueError("必须为单列向量（N x 1）")
    n = matrix.shape[0]  # 获取行数
    if not (1 <= n <= 255):
        raise ValueError("矩阵行数需在1-255之间")

    # 协议头构造
    cmd = 0x0006  # 修改命令码
    # 拓展信息编码：高字节=矩阵编号，低字节=行数
    ext_info = (matrix_id << 8) | (n & 0xFF)

    # 数据打包（保持小端浮点格式）
    data_bytes = b''.join(struct.pack('<f', val) for val in matrix.flatten())

    # 协议字段构造（结构相同）
    length = len(data_bytes) + 2  # 数据长度 + 校验和
    header_bytes = struct.pack('>HHH', cmd, ext_info, length)

    # 校验和计算（算法相同）
    checksum = 0
    for byte in header_bytes + data_bytes:
        checksum += byte
        if checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + 1

    return header_bytes + data_bytes + struct.pack('>H', checksum)


def set_YR(matrix: Union[np.ndarray, list], matrix_id: int = 0) -> bytes:
    """
    发送支路R导纳向量YR（CMD=0x0007）
    协议格式：
    固定头 00 07 | 拓展信息[矩阵编号|行数] | 长度 | 数据 | 校验和
    参数约束：
    - 必须为单列向量（N x 1）
    - 元素为单精度浮点数
    - 矩阵行数范围1-255（用8bit编码）
    """
    # 参数校验
    matrix = np.asarray(matrix, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[1] != 1:  # 校验列数必须为1
        raise ValueError("必须为单列向量（N x 1）")
    n = matrix.shape[0]  # 获取行数
    if not (1 <= n <= 255):
        raise ValueError("矩阵行数需在1-255之间")

    # 协议头构造
    cmd = 0x0007  # 修改命令码
    # 拓展信息编码：高字节=矩阵编号，低字节=行数
    ext_info = (matrix_id << 8) | (n & 0xFF)

    # 数据打包（保持小端浮点格式）
    data_bytes = b''.join(struct.pack('<f', val) for val in matrix.flatten())

    # 协议字段构造（结构相同）
    length = len(data_bytes) + 2  # 数据长度 + 校验和
    header_bytes = struct.pack('>HHH', cmd, ext_info, length)

    # 校验和计算（算法相同）
    checksum = 0
    for byte in header_bytes + data_bytes:
        checksum += byte
        if checksum > 0xFFFF:
            checksum = (checksum & 0xFFFF) + 1

    return header_bytes + data_bytes + struct.pack('>H', checksum)

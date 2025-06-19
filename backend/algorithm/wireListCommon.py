import numpy as np
import itertools
from collections import defaultdict
from backend.algorithm.acclist2A import acclist2A as a2A

# 元件类型属性定义
# 1独立电压源 2L支路 3C支路 4R支路 5开关管(含反并铁二极管) 6二极管 7电流探头 8独立电流源
attrU = 1
attrL = 2
attrC = 3
attrR = 4
attrIGBT = 5
attrDiode = 6
attrIP = 7
attrI = 8

# 默认参数
Rs = 1e-4  # 电压源内阻
Ron = 1e-3  # 管开通电阻
Roff = 1e6  # 管关断电阻
Rwire = 1e-4  # 线电阻
IGBT_Ysw = 0.01  # 开关管LC等效导纳 大于滤波电感导纳且小于滤波电容导纳 0.001<Ysw<200


def post_processing(dt, comps,accList, attrName, attr, observable_data):
    """
    处理接线表解析器共用的后处理逻辑
    :param dt:仿真步长(用于导纳计算)
    :param comps:具有与支路对应器件信息的list，标准参数值的键是’value’(用于矩阵生成)
    :param accList:支路表(用于矩阵生成)
    :param attrName:支路元件名称标记
    :param attr:支路属性标记(用于矩阵生成。原样传出)
    :param observable_data:可观测数据字典(原样传出)
    :return:
    """
    A = a2A(accList)  # 支路-节点矩阵

    # ====================== 矩阵构建 ======================
    igbt_indices = [i for i, a in enumerate(attr) if (a == attrIGBT or a == attrDiode)]
    n_igbt = len(igbt_indices)  # IGBT 数量

    # 生成所有开关状态组合（0=OFF，1=ON）以先后顺序形成字典
    switch_combinations = list(itertools.product([0, 1], repeat=n_igbt))

    # 预存储所有 G 矩阵的字典（以二进制状态为键）
    G_inv_R = {}
    YR = {}

    YL = np.zeros((len(accList), len(accList)))  # 预构建支路列表大小的空矩阵
    for i in range(len(accList)):
        if attr[i] == attrL:
            YL[i, i] = dt / comps[i]['value']

    YC = np.zeros((len(accList), len(accList)))  # 预构建支路列表大小的空矩阵
    for i in range(len(accList)):
        if attr[i] == attrC:
            YC[i, i] = comps[i]['value'] / dt

    for state in switch_combinations:
        YR_d = np.zeros((len(accList), len(accList)))  # 预构建支路列表大小的空矩阵

        for i in range(len(accList)):
            if attr[i] == attrU:
                YR_d[i, i] = 1 / Rs
            if attr[i] == attrR:
                YR_d[i, i] = 1 / comps[i]['value']
            # 动态处理IGBT支路
            if attr[i] == attrIP:
                YR_d[i, i] = 1 / Rwire
            if i in igbt_indices:
                igbt_pos = igbt_indices.index(i)
                switch_state = state[igbt_pos]
                YR_d[i, i] = 1 / (Ron if switch_state == 1 else Roff)

        G_d = A @ YL @ A.T  # 附加电感节点导纳矩阵
        G_d += A @ YC @ A.T  # 附加电容节点导纳矩阵
        G_d += (A @ YR_d @ A.T)  # 附加电阻 节点导纳矩阵
        YR[state] = YR_d  # 预存电阻导纳
        G_inv_R[state] = np.linalg.inv(G_d)  # 预计算逆矩阵

    YR_d = np.zeros((len(accList), len(accList)))  # 预构建支路列表大小的空矩阵

    for i in range(len(accList)):
        if attr[i] == attrU:
            YR_d[i, i] = 1 / Rs
        if attr[i] == attrR:
            YR_d[i, i] = 1 / comps[i]['value']
        # 动态处理IGBT支路
        if attr[i] == attrIP:
            YR_d[i, i] = 1 / Rwire
        if i in igbt_indices:
            YR_d[i, i] = IGBT_Ysw

    G_d = A @ YL @ A.T  # 附加电感节点导纳矩阵
    G_d += A @ YC @ A.T  # 附加电容节点导纳矩阵
    G_d += (A @ YR_d @ A.T)  # 附加电阻 节点导纳矩阵
    G_inv_LC= np.linalg.inv(G_d)  # 预计算逆矩阵


    # ====================== 初始化历史变量 ======================
    J = np.zeros(len(accList))  # 预构建支路列表大小的空矩阵
    for i in range(len(accList)):
        if attr[i] == attrU:
            J[i] = -comps[i]['value'] / Rs
        elif attr[i] == attrI:
            J[i] = comps[i]['value']
        else:
            J[i] = 0


    return [
        observable_data,
        accList,
        attrName,
        attr,
        A,
        n_igbt,
        G_inv_R,
        G_inv_LC,
        YR,
        YL,
        YC,
        J
    ]
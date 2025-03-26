import numpy as np
import itertools
import xml.etree.ElementTree as ET
from collections import defaultdict
from backend.algorithm.acclist2A import acclist2A as a2A

# 元件类型属性定义
# 1独立电压源 2L支路 3C支路 4R支路 5IGBT 6Diode 7电流探头
attrU = 1
attrL = 2  # α = 1 β = 1
attrC = 3  # α = -1 β = 0
attrR = 4
attrIGBT = 5
attrDiode = 6
attrIP = 7

# 默认参数
Rs = 1e-4  # 电压源内阻
Ron = 1e-3  # 管开通电阻
Roff = 1e6  # 管关断电阻
Rwire = 1e-4  # 线电阻


def psimXML(dt, xml_path):
    '''
    :param dt: 仿真步长(s)
    :param xml_path: psim 生成的接线表 xml 文件路径
    :return: list
                0:observable_data 可观测数据列表
                1:accList 支路列表
                2:attr 支路属性列表
                3:A 支路-节点矩阵
                4:n_igbt 可控器件数量
                5:G_inv 导纳矩阵的逆
                6:YR 电阻导纳矩阵
                7:YL 电感导纳矩阵
                8:YC 电容导纳矩阵
                9:J 历史电流源初值
    '''

    def enhanced_parse(xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()

        components = []
        measurement = {'current': [], 'voltage': [], 'Lable': []}
        controllables = []
        node_coords = defaultdict(list)

        # 遍历所有元件
        for comp in root.findall(".//CCircuit/Component"):
            comp_type = comp.get("Type")
            nodes = [n.text.strip() for n in comp.findall("CNode")]

            # 记录测量元件
            if comp_type == "IP":
                measurement['current'].append({
                    'accn': len(components),  # 支路序号
                    'name': comp.get("Name"),
                    'nodes': nodes,
                })
            elif comp_type == "VP2":
                measurement['voltage'].append({
                    'name': comp.get("Name"),
                    'nodes': nodes[:2]
                })
            elif comp_type == "Label":
                measurement['Lable'].append({
                    'name': comp.get("Name"),
                    'nodes': nodes[:2]
                })

            # 记录可控制元件
            if comp_type == "IGBT":
                controllables.append({
                    'nodes': nodes[:2]
                })
            elif comp_type == "MOSFET":
                controllables.append({
                    'nodes': nodes[:2]
                })

            # 定义元件类型与对应参数的映射表
            type_to_param = {
                'C': 'Capacitance',
                'R': 'Resistance',
                'VDC': 'Amplitude',
                'L': 'Inductance',
            }

            # --- 提取参数值 ---
            value = None
            if comp_type in type_to_param:
                param_name = type_to_param[comp_type]
                param_node = comp.find(f".//Param[@Name='{param_name}']")
                if param_node is not None:
                    value = float(param_node.text)

            # 定义支路属性映射表
            type_mapping = {
                'R': attrR,
                'L': attrL,
                'C': attrC,
                'IGBT': attrIGBT,
                'DIODE': attrDiode,
                'VDC': attrU,
                'IP': attrIP,
                'VP2': None
            }

            # 生成有效支路
            if type_mapping.get(comp_type, None) is not None:
                component_data = {
                    'type': comp_type,
                    'nodes': nodes,
                    'attr': type_mapping[comp_type]
                }
                # 如果存在 value，则添加字段
                if value is not None:
                    component_data['value'] = value
                components.append(component_data)

        return components, measurement

    # 解析XML文件
    netlist = enhanced_parse(xml_path)

    # 收集被删除的节点数值（仅IGBT类型的第三个节点）
    deleted_nodes = set()
    for comp in netlist[0]:
        if comp['type'] == 'IGBT' and len(comp['nodes']) >= 3:
            deleted_node = comp['nodes'][2]
            deleted_nodes.add(int(deleted_node))

    sorted_deleted = sorted(deleted_nodes)
    new_data = []

    # 依据删除节点调整支路列表
    for comp in netlist[0]:
        # 截断 nodes 到前两个元素
        truncated_nodes = comp['nodes'][:2]
        # 调整节点号：数值减去所有 <= 当前节点号的被删除节点数
        adjusted_nodes = []
        for node in truncated_nodes:
            n = int(node)
            k = sum(1 for x in sorted_deleted if x <= n)
            adjusted_n = n - k
            adjusted_nodes.append(str(adjusted_n))
        # 保留原字典所有字段（包括 value），仅更新 nodes
        new_comp = {**comp, 'nodes': adjusted_nodes}
        new_data.append(new_comp)

    # 依据删除节点调整量测列表
    for key in netlist[1]:
        for item in netlist[1][key]:
            adjusted_nodes = []
            for node in item['nodes']:
                n = int(node)
                # 对节点值进行调整
                for del_node in sorted_deleted:
                    if n > del_node:
                        n -= 1
                adjusted_nodes.append(str(n))
            item['nodes'] = adjusted_nodes

    accList = [[int(node) for node in item['nodes']] for item in new_data]
    attr = [item['attr'] for item in new_data]

    # 处理独立电压源，针对没有放置G地标志的情况
    has_zero = any(0 in pair for pair in accList)
    if not has_zero:
        # 找到第一个attr值为attrU的索引
        target_index = next((i for i, a in enumerate(attr) if a == 1), None)
        if target_index is not None:
            # 获取对应的两个节点值，并取较小值作为vl
            node_pair = accList[target_index]
            vl = node_pair[1]

            # 遍历整个accList，替换vl为0，且所有大于vl的值减1
            new_accList = []
            for pair in accList:
                new_pair = []
                for num in pair:
                    if num == vl:
                        new_pair.append(0)
                    elif num > vl:
                        new_pair.append(num - 1)
                    else:
                        new_pair.append(num)
                new_accList.append(new_pair)
            accList = new_accList

            # 遍历整个量测列表，替换vl为0，且所有大于vl的值减1
            for key in netlist[1]:
                for item in netlist[1][key]:
                    new_pair = []
                    for num in item['nodes']:
                        n = int(num)
                        # 对节点值进行调整
                        if n == vl:
                            new_pair.append(0)
                        elif n > vl:
                            new_pair.append(n - 1)
                        else:
                            new_pair.append(n)
                    item['nodes'] = new_pair

    A = a2A(accList)  # 支路-节点矩阵

    # ====================== 矩阵构建 ======================
    igbt_indices = [i for i, a in enumerate(attr) if (a == attrIGBT or a == attrDiode)]
    n_igbt = len(igbt_indices)  # IGBT 数量

    # 生成所有开关状态组合（0=OFF，1=ON）以先后顺序形成字典
    switch_combinations = list(itertools.product([0, 1], repeat=n_igbt))

    # 预存储所有 G 矩阵的字典（以二进制状态为键）
    G_inv = {}
    YR = {}

    YL = np.zeros((len(accList), len(accList)))  # 预构建支路列表大小的空矩阵
    for i in range(len(accList)):
        if attr[i] == attrL:
            YL[i, i] = dt / new_data[i]['value']

    YC = np.zeros((len(accList), len(accList)))  # 预构建支路列表大小的空矩阵
    for i in range(len(accList)):
        if attr[i] == attrC:
            YC[i, i] = new_data[i]['value'] / dt

    for state in switch_combinations:
        YR_d = np.zeros((len(accList), len(accList)))  # 预构建支路列表大小的空矩阵

        for i in range(len(accList)):
            if attr[i] == attrU:
                YR_d[i, i] = 1 / Rs
            if attr[i] == attrR:
                YR_d[i, i] = 1 / new_data[i]['value']
            # 动态处理IGBT支路
            if attr[i] == attrIP:
                YR_d[i, i] = 1 / Rwire
            if i in igbt_indices:
                igbt_pos = igbt_indices.index(i)
                switch_state = state[igbt_pos]
                YR_d[i, i] = 1 / (Ron if switch_state == 1 else Roff)

        G_d = A @ YL @ A.T  # 附加电感节点导纳矩阵
        G_d += A @ YC @ A.T  # 附加电容节点导纳矩阵
        G_d += (A @ YR_d @ A.T)  # 附加电阻节点导纳矩阵
        YR[state] = YR_d  # 预存电阻导纳
        G_inv[state] = np.linalg.inv(G_d)  # 预计算逆矩阵

    # ====================== 初始化历史变量 ======================
    J = np.zeros(len(accList))  # 预构建支路列表大小的空矩阵
    for i in range(len(accList)):
        if attr[i] == attrU:
            J[i] = -new_data[i]['value'] / Rs
        else:
            J[i] = 0

    return netlist[1], accList, attr, A, n_igbt, G_inv, YR, YL, YC, J


# 调用示例
if __name__ == "__main__":
    dt = 1e-6  # 仿真步长
    xml_file_path = "./buckboost.xml"  # XML文件路径
    results = psimXML(dt, xml_file_path)

    # 可以根据需要对结果进行处理
    observable_data, accList, attr, A, n_igbt, G_inv, YR, YL, YC, J = results

import re
import json
from backend.algorithm.wireListCommon import *

import sys
import os
def GetPath():
    # 动态获取当前.exe所在的目录，确保能正确加载资源文件
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe文件运行，'frozen' 属性会被设置
        app_dir = sys._MEIPASS
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录
    return app_dir  # 用法为os.path.join(app_dir, 'aoz2p.ico') os.path.join(GetPath(), 'aoz2p.ico')

def pspiceNET(dt, net_path):
    """
    :param dt: 仿真步长(s)
    :param net_path: psim 生成的接线表 xml 文件路径
    :return: list
                0:observable_data 可观测数据列表
                1:accList 支路列表
                2:attr 支路属性列表
                3:A 支路-节点矩阵
                4:n_igbt 可控器件数量
                5:G_inv_R R策略导纳矩阵的逆
                6:G_inv_LC LC策略导纳矩阵的逆
                7:YR 电阻导纳矩阵
                8:YL 电感导纳矩阵
                9:YC 电容导纳矩阵
                10:J 历史电流源初值
    """

    comp_org = []  # 存储解析后的元件信息

    type_cfg = {
        'V': {"node_num": 2, "attr": attrU},
        'R': {"node_num": 2, "attr": attrR},
        'L': {"node_num": 2, "attr": attrL},
        'C': {"node_num": 2, "attr": attrC},
        'D': {"node_num": 2, "attr": attrDiode},
        'Q': {"node_num": 3, "attr": attrIGBT},
    }

    # 模型配置
    with open(GetPath()+'./syscfg/pspiceModel.json', 'r') as json_file:
        model_config = json.load(json_file)

    def parse_value(s):
        """从字符串中提取浮点数（如'10u'→1e-5, '5Vdc'→5.0）"""
        match = re.match(r'^([-+]?\d+\.?\d*([eE][-+]?\d+)?)', s.strip())
        return float(match.group(1)) if match else 0.0

    def enhanced_parse(parts):
        if not parts:
            return

        comp_type = parts[0][0].upper()
        comp_name = parts[0][1:] if '_' in parts[0] else parts[0]
        component_data = None

        if comp_type in type_cfg:
            # 处理基本元件类型
            node_num = type_cfg[comp_type]["node_num"]
            nodes = parts[1:1 + node_num]
            value = 0.0
            # 根据元件类型提取值
            if comp_type in ['V', 'R', 'C']:
                # 值在第4个字段（parts[3]）
                if len(parts) >= 4:
                    value_str = parts[3]
                    value = parse_value(value_str)
            elif comp_type == 'L':
                # 值在最后一个字段
                if len(parts) > 1 + node_num:
                    value_str = parts[-1]
                    value = parse_value(value_str)
            component_data = {
                'type': comp_type,
                'name': comp_name,
                'nodes': nodes,
                'attr': type_cfg[comp_type]["attr"],
                'value': value,
            }
        elif comp_type == 'X':
            # 处理子电路元件
            model_name = None
            model_info = None
            nodes = []
            # 查找模型名及其位置
            for i in range(1, len(parts)):
                candidate = parts[i]
                if candidate in model_config["model_definitions"]:
                    model_name = candidate
                    model_info = model_config["model_definitions"][model_name]
                    node_num = model_info["node_num"]
                    # 提取节点并验证数量
                    if len(parts[1:i]) != node_num:
                        print(f"Error: 节点数不符于模型 {model_name} 的 node_num")
                        return
                    nodes = parts[1:i]
                    break
            if not model_name:
                print(f"Warning: 未找到模型定义 {parts}")
                return

            # 确定元件类型和属性
            model_type = model_info["type"]
            attr = type_cfg.get(model_type, {}).get("attr")
            if attr is None:
                print(f"Warning: 未定义类型 {model_type} 的属性")
                return

            component_data = {
                'type': model_type,
                'name': comp_name,
                'nodes': nodes,
                'attr': attr,
                'value': 0.0,  # 子电路元件值暂不处理
            }

        if component_data:
            comp_org.append(component_data)

    def parse_netlist(net_path_r):
        current_block = []
        with open(net_path_r, 'r') as f:
            for line in f:
                # 去除注释和空白
                line = line.split('*')[0].strip()
                if not line:
                    continue

                # 处理续行符
                if line.startswith('+'):
                    if current_block:
                        current_block[-1] += ' ' + line[1:].strip()
                else:
                    if current_block:
                        enhanced_parse(current_block)
                    current_block = re.split(r'\s+', line.strip())

            if current_block:
                enhanced_parse(current_block)

    def remove_igbt_control_nodes(comp_org):
        # 复制原始列表以避免修改原始数据
        components = [comp.copy() for comp in comp_org]

        # 步骤1：处理所有IGBT，删除第二个节点并收集被删除的节点
        removed_nodes = set()
        for comp in components:
            if comp['type'] == 'Q':
                if len(comp['nodes']) >= 2:
                    # 记录被删除的第二个节点
                    removed_node = comp['nodes'][1]
                    removed_nodes.add(removed_node)
                    # 修改节点列表
                    comp['nodes'] = [comp['nodes'][0]] + comp['nodes'][2:]

        # 步骤2：递归删除所有包含被移除节点及相关悬空器件
        nodes_to_remove = removed_nodes.copy()
        components_to_remove = set()

        # 使用循环处理所有级联删除
        while True:
            # 查找包含待删除节点的元件
            current_round_components = set()
            for i, comp in enumerate(components):
                if i in components_to_remove:
                    continue
                for node in comp['nodes']:
                    if node in nodes_to_remove:
                        current_round_components.add(i)
                        break

            if not current_round_components:
                break  # 没有更多需要删除的元件

            # 记录这些元件中的所有节点
            affected_nodes = set()
            for i in current_round_components:
                affected_nodes.update(components[i]['nodes'])
            components_to_remove.update(current_round_components)

            # 检查这些节点的剩余连接情况
            node_refcount = {}
            for i, comp in enumerate(components):
                if i in components_to_remove:
                    continue
                for node in comp['nodes']:
                    node_refcount[node] = node_refcount.get(node, 0) + 1

            # 找出所有悬空节点（引用次数不大于1）
            new_nodes_to_remove = {
                node for node in affected_nodes
                if node_refcount.get(node, 0) <= 1
            }
            nodes_to_remove.update(new_nodes_to_remove)

        # 生成最终保留的元件列表
        final_components = [
            comp for i, comp in enumerate(components)
            if i not in components_to_remove
        ]

        return final_components

    def process_nodes_and_labels(components):
        # 收集所有节点并分类
        all_nodes = set()
        for comp in components:
            for node in comp['nodes']:
                all_nodes.add(str(node))  # 确保字符串类型处理

        # 创建节点映射表和标签记录
        node_mapping = {}
        label_info = []
        current_id = 1  # 非数字节点从1开始编号

        # 处理数字节点
        for node in sorted(all_nodes, key=lambda x: (not x.isdigit(), x)):
            if node.isdigit():
                node_mapping[node] = int(node)
            else:
                node_mapping[node] = current_id
                # 检测输出节点（不区分大小写）
                if 'out' in node.lower():
                    label_info.append({'name': node, 'nodes': [current_id]})
                current_id += 1

        # 执行节点替换
        for comp in components:
            comp['nodes'] = [node_mapping[str(node)] for node in comp['nodes']]

        return components, label_info

    def build_measurement(components, labels):
        measurement = {
            'current': [],
            'voltage': [],
            'label': labels
        }

        accn_counter = 1
        for comp in components:
            if comp['type'] in ['R', 'L', 'C']:
                # 构建current/voltage条目
                entry = {
                    'accn': accn_counter,
                    'name': comp['name'],
                    'nodes': comp['nodes']
                }
                measurement['current'].append(entry)
                measurement['voltage'].append(entry)
                accn_counter += 1

        return measurement

    # 开始执行
    parse_netlist(net_path)

    # 执行清理
    cleaned_components = remove_igbt_control_nodes(comp_org)

    comps, labels = process_nodes_and_labels(cleaned_components)

    meass = build_measurement(comps, labels)

    accList = [[int(node) for node in item['nodes']] for item in comps]
    attr = [item['attr'] for item in comps]
    attrName = [item['name'][1:] if item['name'].startswith('_') else item['name'] for item in comps]

    return post_processing(dt, comps, accList, attrName, attr, meass)


# 调用示例
if __name__ == "__main__":
    tdt = 1e-6  # 仿真步长
    net_file_path = "./twList/buckboost.net"
    results = pspiceNET(tdt, net_file_path)

    # 可以根据需要对结果进行处理
    observable_data, accList, attrName, attr, A, n_igbt, G_inv_R, G_inv_LC, YR, YL, YC, J = results

    print("OVER")

import numpy as np


def acclist2A(accList):
    """
    根据支路列表 `accList` 生成节点支路关联矩阵 A。

    Parameters:
        accList (list of list/tuple): 支路列表，每个元素为二元组/列表，表示支路的起点和终点。
                                      节点编号必须为非负整数，且不允许自环（起点≠终点）。

    Returns:
        np.ndarray: 节点支路关联矩阵 A，形状为 (max_node, len(accList))，dtype=np.float64。

    Raises:
        TypeError: 如果输入类型不符合要求。
        ValueError: 如果支路结构或节点编号非法。
    """
    # 检查 accList 是否为列表
    if not isinstance(accList, list):
        raise TypeError("accList 必须是一个列表（list）")

    # 遍历每条支路，检查格式和内容
    for i, edge in enumerate(accList):
        # 检查是否为列表或元组
        if not isinstance(edge, (list, tuple)):
            raise TypeError(f"支路 {i} 必须是列表或元组，实际类型: {type(edge)}")
        # 检查支路长度是否为2
        if len(edge) != 2:
            raise ValueError(f"支路 {i} 必须包含两个节点，实际长度: {len(edge)}")
        start, end = edge
        # 检查节点是否为整数
        if not isinstance(start, int) or not isinstance(end, int):
            raise TypeError(f"支路 {i} 的节点必须为整数，实际值: ({start}, {end})")
        # 检查节点编号非负
        if start < 0 or end < 0:
            raise ValueError(f"支路 {i} 的节点不能为负数，实际值: ({start}, {end})")
        # 检查是否存在自环（起点≠终点）
        if start == end:
            raise ValueError(f"支路 {i} 是自环（起点和终点相同: {start}）")

    # 确定最大节点编号（至少为0）
    max_node = max(max(edge) for edge in accList) if accList else 0
    rows = max_node  # 行数 = 最大节点编号（忽略参考节点0）
    cols = len(accList)

    # 初始化全零矩阵
    A = np.zeros((rows, cols), dtype=np.float64)

    # 填充矩阵
    for col, (start, end) in enumerate(accList):
        # 处理起点（流出节点，对应-1）
        if start != 0:
            A[start - 1, col] = -1
        # 处理终点（流入节点，对应+1）
        if end != 0:
            A[end - 1, col] = 1
    return A

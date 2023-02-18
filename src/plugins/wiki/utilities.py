def _get_item(ls: list, item: int):
    """
    为列表实现类似字典的get方法
    :param ls: 要查询的列表
    :param item: 元素的下标
    :return: 若元素存在，返回该元素；否则返回None
    """
    try:
        return ls[item]
    except IndexError:
        return None


def _startswith(string: str, prefix: str) -> bool:
    """
    替换原版的startswith方法
    :param string: 要检测的字符串
    :param prefix: 要检测的前缀，字符串中的每个字符都将被单独检测
    :return: 判定结果
    """
    if not string:
        return False
    for i in prefix:
        if string.startswith(i):
            return True
    return False

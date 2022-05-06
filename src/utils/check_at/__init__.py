from json import loads


def check_at(data: str) -> list:
    """
    检测at了谁，返回[qq, qq, qq,...]
    包含全体成员直接返回['all']
    如果没有at任何人，返回[]
    来自 https://github.dev/yzyyz1387/nonebot_plugin_admin
    :param data: event.json
    :return: list
    """
    try:
        qq_list = []
        data = loads(data)
        for msg in data["message"]:
            if msg["type"] == "at":
                if 'all' not in str(msg):
                    qq_list.append(int(msg["data"]["qq"]))
                else:
                    return ['all']
        return qq_list
    except KeyError:
        return []

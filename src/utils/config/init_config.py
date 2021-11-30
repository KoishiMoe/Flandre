import copy
from pathlib import Path

from yaml import safe_load, safe_dump

DEFAULT_CONFIG = {
    'BotConfig':
        {
            'port': 8080,
            'debug': False,
            'superusers': [""],
            'nickname': ["芙兰", "芙兰朵露", "芙兰朵露·斯卡蕾特", "Flandre"],
            'command_start': ["", "/"],
            'command_sep': ["."],
            'session_expire_timeout': 60,
            # 'log_level': 0,
            'use_local_help': False,
        },

    'WithdrawConfig':
        {
            'max_withdraw_num': 50,
        },
    'Pixiv':
        {
            'max_pic_num': 20,
            'use_forward_msg': True,
            'token': '',
            'enable_tag_filter': True,
            'blocked_tags': ["R18", "R-18", "R-18G", "R18G"],
            'proxy': '',
        },
    'b23Extract':
        {
            'sessdata': '',
            'bili_jct': '',
            'buvid3': '',
            'http_proxy': '',
        },

}


class Initcfg:
    @staticmethod
    def new_config(path: Path):
        try:
            with open(path, 'w', encoding='utf-8') as w:
                w.write(safe_dump(DEFAULT_CONFIG).encode('utf-8').decode('unicode-escape'))  # 防止中文被输出为转义字符
            return True
        except PermissionError as e:
            return "初始化配置文件错误：没有写权限"
        except IsADirectoryError as e:
            return "初始化配置文件错误：已有名为'config.yaml'的目录存在，请删除或重命名该目录"
        except Exception as e:
            return f"初始化配置文件错误：未知错误\n{e}"

    @staticmethod
    def update_config(path: Path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                conf: dict = safe_load(f)
                new_conf = copy.deepcopy(conf)
            with open(path, 'w', encoding='utf-8') as f:
                for i in DEFAULT_CONFIG.keys():
                    if i in conf.keys():
                        for j in DEFAULT_CONFIG.get(i, {}).keys():
                            if not conf[i]:
                                new_conf[i] = DEFAULT_CONFIG[i]
                            elif j not in conf[i].keys():
                                new_conf[i][j] = DEFAULT_CONFIG[i][j]
                    else:
                        new_conf[i] = DEFAULT_CONFIG[i]
                f.write(safe_dump(new_conf).encode('utf-8').decode('unicode-escape').replace("null", ''))
                # 出现null会导致加载失败
            return True
        except PermissionError as e:
            return "更新配置文件错误：没有写权限"
        except Exception as e:
            return f"更新配置文件错误：未知错误\n{e}"

    @staticmethod
    def check_config(conf: dict) -> bool:
        """检查配置文件是否需要更新"""
        for i in DEFAULT_CONFIG.keys():
            if i not in conf.keys():
                return False
            else:
                for j in DEFAULT_CONFIG.get(i, {}).keys():
                    if not conf[i] or j not in conf[i].keys():
                        return False
        return True

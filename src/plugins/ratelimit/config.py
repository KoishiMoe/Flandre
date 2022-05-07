import os
from json import dumps, loads
from pathlib import Path

from nonebot import get_driver

CFG_PATH = Path(".") / "data" / "database" / "rate_limit"
CFG_FILE = CFG_PATH / "config.json"

cfg = {}

driver = get_driver()


@driver.on_startup
async def _init_cfg():
    global cfg

    os.makedirs(CFG_PATH, exist_ok=True)
    if not CFG_FILE.is_file():
        _save_file()

    cfg = _get_cfg_from_file()


def _get_cfg_from_file() -> dict:
    data = loads(CFG_FILE.read_bytes())
    return data


def _save_file():
    with open(CFG_FILE, "w", encoding="utf-8") as w:
        w.write(dumps(cfg, indent=4))


def get_config(service: str, limit_type: int, daily: bool, gid: int = None) -> int:
    """
    根据指定的参数获取频率限制配置
    :param service: 限制的服务名称
    :param limit_type: 限制类型，1为全局限制，2为群限制，3为用户限制
    :param daily: 若为True,获取日限制
    :param gid: 群号，仅当limit_type==2时有效
    :return: int 若daily==False返回cd（单位：秒），daily==True则返回每日限额（单位：次）
    """
    srv_config = cfg.get(service)
    gid = str(gid) if gid else gid  # 转成字符串，因为从json里读出来的是字符串

    if srv_config:
        daily_or_cd_limit_cfg = srv_config.get("daily" if daily else "cd")
        if daily_or_cd_limit_cfg:
            match limit_type:
                case 1:
                    return daily_or_cd_limit_cfg.get("global", 0)
                case 2:
                    group_limit = daily_or_cd_limit_cfg.get("group")
                    if group_limit:
                        if gid:
                            return group_limit.get(gid, 0)
                        else:
                            return group_limit.get("0", 0)
                case 3:
                    return daily_or_cd_limit_cfg.get("user", 0)

    return 0


def modify_config(value: int, service: str, limit_type: int, daily: bool, gid: int = None):
    """
    根据指定的参数修改频率限制配置
    :param value: 新的值，必须>=0且为整数
    :param service: 限制的服务名称
    :param limit_type: 限制类型，1为全局限制，2为群限制，3为用户限制
    :param daily: 若为True,获取日限制
    :param gid: 群号，仅当limit_type==2时有效
    :return: None
    :raises: ValueError 当value<0时
    """
    if value < 0:
        raise ValueError(f"频率限制的值必须为大于0的整数，而传入的值为{value}")

    gid = str(gid) if gid else gid
    global cfg

    srv_config = cfg.get(service)
    if not srv_config:
        cfg[service] = {}
        srv_config = cfg[service]

    daily_or_cd = "daily" if daily else "cd"
    daily_or_cd_limit_cfg = srv_config.get(daily_or_cd)
    if not daily_or_cd_limit_cfg:
        srv_config[daily_or_cd] = {}
        daily_or_cd_limit_cfg = srv_config[daily_or_cd]

    match limit_type:
        case 1:
            daily_or_cd_limit_cfg["global"] = value
        case 2:
            group_limit = daily_or_cd_limit_cfg.get("group")
            if not group_limit:
                daily_or_cd_limit_cfg["group"] = {}
                group_limit = daily_or_cd_limit_cfg["group"]
            group_limit[gid] = value
        case 3:
            daily_or_cd_limit_cfg["user"] = value

    _save_file()

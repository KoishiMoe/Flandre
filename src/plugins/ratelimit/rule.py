from datetime import date
from time import time

from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.permission import SUPERUSER
from nonebot.plugin import export
from nonebot.rule import Rule

from .config import get_config

record = {}
services = {}


@export()
def limit(service: str) -> Rule:
    """
    用于频率检查的rule。一般来说，为了提供频率限制的提示，建议使用check_limit函数（返回bool）
    :param service: 服务名
    :return: Rule
    """

    async def _limit(bot: Bot, event: Event):
        return await check_limit(bot, event, service)

    return Rule(_limit)


@export()
async def check_limit(bot: Bot, event: Event, service: str, add_count: bool = True) -> bool:
    """
    检查是否达到频率限制。如果需要用于事件响应器的rule,请使用limit函数
    :param bot:
    :param event:
    :param service: 服务名
    :param add_count: 是否增加计数。当需要动态增加计数时，请传入False，在执行成功后再传入True
    :return: bool 未达到限制返回True
    """
    global record
    if not record:
        record = {srv: {
            "cd": {
                "global": 0,
                "groups": {},
                "users": {}
            },
            "daily": {
                "global": 0,
                "groups": {},
                "users": {}
            }
        } for srv in services}
        record["__date__"] = str(date.today())

    if record["__date__"] != str(date.today()):
        for k, v in record.items():
            if k != "__date__":
                v["daily"] = {
                    "global": 0,
                    "groups": {},
                    "users": {}
                }
        record["__date__"] = str(date.today())

    try:
        if await SUPERUSER(bot, event):
            return True
    except Exception as e:
        logger.debug(f"判定{service}的频率限制时，超级用户权限检查失败：{e}。事件为：{event.json()}")

    service_record = record[service]
    global_flag, group_flag, user_flag = False, False, False
    try:
        global_cd = get_config(service, 1, False)
        global_daily = get_config(service, 1, True)
        global_cd_record = service_record["cd"]["global"]
        global_daily_record = service_record["daily"]["global"]
        if global_cd and time() - global_cd_record < global_cd:
            return False
        if global_daily and global_daily_record >= global_daily:
            return False
        global_flag = True
    except Exception as e:
        logger.info(f"判定{service}的频率限制时， 全局限制检查失败：{e}。事件为：{event.json()}")
    try:
        user_cd = get_config(service, 3, False)
        user_daily = get_config(service, 3, True)
        user_id = int(event.get_user_id())
        user_cd_record = service_record["cd"]["users"].get(user_id, 0)
        user_daily_record = service_record["daily"]["users"].get(user_id, 0)

        if user_cd and time() - user_cd_record < user_cd:
            return False
        if user_daily and user_daily_record >= user_daily:
            return False
        user_flag = True
    except Exception as e:
        logger.debug(f"判定{service}的频率限制时，用户限制检查失败：{e}。事件为：{event.json()}")
    try:
        if isinstance(event, GroupMessageEvent):
            group_id = event.group_id
            group_cd = get_config(service, 2, False, group_id) or get_config(service, 2, False, 0)
            group_daily = get_config(service, 2, True, group_id) or get_config(service, 2, True, 0)
            group_cd_record = service_record["cd"]["groups"].get(group_id, 0)
            group_daily_record = service_record["daily"]["groups"].get(group_id, 0)

            if group_cd and time() - group_cd_record < group_cd:
                return False
            if group_daily and group_daily_record >= group_daily:
                return False
            group_flag = True
    except Exception as e:
        logger.warning(f"判定{service}的频率限制时，群限制检查失败：{e}。事件为：{event.json()}")

    if add_count:
        if global_flag:
            service_record["cd"]["global"] = time()
            service_record["daily"]["global"] = global_daily_record + 1
        if user_flag:
            service_record["cd"]["users"][user_id] = time()
            service_record["daily"]["users"][user_id] = user_daily_record + 1
        if group_flag:
            service_record["cd"]["groups"][group_id] = time()
            service_record["daily"]["groups"][group_id] = group_daily_record + 1
    return True


@export()
def register(service: str, desc: str = ""):
    if service in services.keys():
        logger.warning(f"频率限制：有多个插件注册了同一服务名：{service}，请检查是否有插件冲突")
    services[service] = desc

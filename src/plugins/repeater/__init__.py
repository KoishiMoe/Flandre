from random import choice
from typing import Callable

from nonebot import on_message, on_endswith
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.plugin import require

# 接入服务管理器
register: Callable = require("service").register
online: Callable = require("service").online

register("repeater", "人类的本质")

# 接入帮助系统
__usage__ = """
            触发方法：
            1. 在群里复读，3次之后bot有50%的概率复读一次
            2. 发送感叹号结尾的语句，如果总长度不超过16（含感叹号），bot会将其复读三次
            """

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = '人类的本质'

record = {}

multi_repeater = on_message(rule=online("repeater"), priority=12, block=False)


@multi_repeater.handle()
async def _multi(bot: Bot, event: MessageEvent):
    if not isinstance(event, GroupMessageEvent):
        return
    gid = str(event.group_id)
    msg = str(event.message).strip()
    group_record = record.get(gid)
    if not group_record:
        record[gid] = {
            "last": msg,
            "time": 1,
            "repeated": False,
        }
    else:
        if group_record["last"] == msg:
            group_record["time"] += 1
        else:
            group_record["last"] = msg
            group_record["time"] = 1
            group_record["repeated"] = False
        if group_record["time"] >= 3 and not group_record["repeated"]:
            if choice((True, False)):
                group_record["repeated"] = True
                group_record["time"] += 1
                await multi_repeater.finish(msg)


exclamation_repeater = on_endswith(("!", "！"), rule=online("repeater"), priority=12, block=False)


@exclamation_repeater.handle()
async def _ex(bot: Bot, event: MessageEvent):
    if not isinstance(event, GroupMessageEvent):
        return
    msg = str(event.message).strip()
    if len(msg) <= 16:
        await exclamation_repeater.finish(msg * 3)

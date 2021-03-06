from random import choice

from nonebot import on_message, on_endswith
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.plugin import require

# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

register("repeater", "人类的本质")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag

# 接入频率限制
require("ratelimit")
from ..ratelimit.config_manager import register as register_ratelimit
from ..ratelimit.rule import limit

register_ratelimit("repeater", "复读姬")

# 接入帮助系统
__usage__ = """
触发方法：
1. 在群里复读，3次之后bot有50%的概率复读一次
2. 发送感叹号结尾的语句，如果总长度不超过16（含感叹号），bot会将其复读三次
"""

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = '人类的本质'

record = {}

multi_repeater = on_message(rule=online("repeater") & gag() & limit("repeater"), priority=12, block=False)


@multi_repeater.handle()
async def _multi(bot: Bot, event: GroupMessageEvent):
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


exclamation_repeater = on_endswith(("!", "！"), rule=online("repeater") & gag() & limit("repeater"),
                                   priority=12, block=False)


@exclamation_repeater.handle()
async def _ex(bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip()
    if len(msg) <= 16:
        await exclamation_repeater.finish(msg * 3)

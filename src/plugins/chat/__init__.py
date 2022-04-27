from typing import Callable

from nonebot import Bot, on_message
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.plugin import require

from . import admin
from .replyer import reply_handler
from .rule import get_matcher

# 接入服务管理器
register: Callable = require("service").register
online: Callable = require("service").online

register("chat", "闲聊")

# 接入帮助系统
__usage__ = '直接@bot，随便说点什么，即可开始尬聊（不是）\n' \
            '配置功能的帮助请使用chat.help查看'

__help_version__ = '0.0.2 (Flandre)'

__help_plugin_name__ = '聊天'

chat = on_message(priority=11, rule=online("chat"), block=False)


@chat.handle()
async def _chat(bot: Bot, event: MessageEvent):
    matcher = await get_matcher(event)
    if matcher:
        await reply_handler(bot, event, matcher.get("reply", {}), matcher.get("config", {}))

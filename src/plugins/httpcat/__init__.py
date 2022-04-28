from typing import Callable

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment, Message
from nonebot.plugin import require

# 接入帮助系统
__usage__ = 'http.cat： httpcat [http状态码]\n' \
            '注意状态码仅支持标准RFC'

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = 'httpcat'

# 接入服务管理器
register: Callable = require("service").register
online: Callable = require("service").online

register("httpcat", "获取Http状态码猫猫图")

http_cat = on_command("httpcat", rule=online("httpcat"))


@http_cat.handle()
async def _http_cat(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()[7:].lstrip()
    if msg.isnumeric() and len(msg) == 3:
        image = MessageSegment.image(f'https://http.cat/{msg}')
        await bot.send(event, message=Message(image))

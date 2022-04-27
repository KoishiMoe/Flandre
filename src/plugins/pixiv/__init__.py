import asyncio
import re
from typing import Callable

from nonebot import on_startswith
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, GroupMessageEvent
from nonebot.plugin import require

from src.utils.config import BotConfig, PixivConfig
from .data_source import Pixiv

# 接入服务管理器
register: Callable = require("service").register
online: Callable = require("service").online

register("pixiv", "P站图获取")

# 接入帮助系统
__usage__ = '#pixiv [插画id或链接]'

__help_version__ = '0.2.0 (Flandre)'

__help_plugin_name__ = 'Pixiv'

get_pixiv = on_startswith("#pixiv", ignorecase=True, rule=online("pixiv"))


@get_pixiv.handle()
async def _get_pixiv(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()[6:].lstrip()  # 命令长度是6,从第七个开始取……
    if not msg.isnumeric():
        num = re.search(r'artworks/\d+', msg)
        if num:
            msg = num.group().lstrip('artworks/')
        else:
            return

    await bot.send(event, message=Message("正在获取图片，请稍候……"))

    images = await Pixiv.get_pic(msg)
    if not images:
        await bot.send(event, message=Message("没有找到该图片的说……"))
    elif len(images) > 5 and PixivConfig.use_forward_msg and isinstance(event, GroupMessageEvent):  # 似乎私聊不支持合并转发
        messages = await _fake_msg(images, bot.self_id)
        await bot.send_group_forward_msg(group_id=event.group_id, messages=messages)
    else:
        for image in images:
            await bot.send(event, Message(image))
            await asyncio.sleep(3)


async def _fake_msg(images: list, qq: str):
    node = []

    for i in images:
        name = list(BotConfig.nickname)[0] if BotConfig.nickname else '芙兰'
        content = i
        dic = {"type": "node", "data": {"name": name, "uin": qq, "content": content}}
        node.append(dic)

    return node

import asyncio
import re

from nonebot import on_command
from nonebot.adapters.cqhttp import Bot, MessageEvent, Message, GroupMessageEvent
from nonebot.typing import T_State

from src.utils.config import BotConfig, PixivConfig
from .data_source import Pixiv

# 接入帮助系统
__usage__ = '#pixiv [插画id或链接]'

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = 'Pixiv'

get_pixiv = on_command("#pixiv", aliases={"#Pixiv", "#P站", "p站", "#p站图", "#P站图"})


@get_pixiv.handle()
async def _get_pixiv(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.message).strip()
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
    node = list()

    for i in images:
        name = list(BotConfig.nickname)[0] if BotConfig.nickname else '芙兰'
        content = i
        dic = {"type": "node", "data": {"name": name, "uin": qq, "content": content}}
        node.append(dic)

    return node

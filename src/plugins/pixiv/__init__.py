import asyncio
import re

from nonebot.adapters.cqhttp import Bot, MessageEvent, MessageSegment, Message
from nonebot import on_command
from nonebot.typing import T_State

from .data_source import Pixiv

get_pixiv = on_command("#pixiv", aliases={"#Pixiv", "#P站", "p站", "#p站图", "#P站图"})


@get_pixiv.handle()
async def _get_pixiv(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.message).strip()
    if not msg.isnumeric():
        num = re.search(r'artworks/\d+', msg)
        if num:
            msg = num.group().lstrip('artworks')
        else:
            return

    await bot.send(event, message=Message("正在获取图片，请稍候……"))

    images = await Pixiv.get_pic(msg)
    if not images:
        await bot.send(event, message=Message("没有找到该图片的说……"))
    for image in images:
        await bot.send(event, Message(image))
        await asyncio.sleep(3)

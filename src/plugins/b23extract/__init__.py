import re

from bilibili_api import bvid2aid
from nonebot import on_regex
from nonebot.adapters.cqhttp import Bot, Message, MessageEvent
from nonebot.typing import T_State

from .data_source import Extract

# b23_extract = on_regex(r"(b23.tv)|(bili(22|23|33|2233).cn)|(live.bilibili.com)|(bilibili.com/(video|read|bangumi))|("
#                        r"^(av|cv)(\d+))|(^BV([a-zA-Z0-9]{10})+)|(\[\[QQ小程序\]哔哩哔哩\])|(QQ小程序&amp;#93;哔哩哔哩)|("
#                        r"QQ小程序&#93;哔哩哔哩)", flags=re.I)
#
#
# @b23_extract.handle()
# async def _b23_extract(bot: Bot, event: MessageEvent, state: T_State):
#     message = str(event.message).strip()


bv_extract = on_regex(r"(^BV[a-zA-Z0-9]{10})", flags=re.I)


@bv_extract.handle()
async def _bv_extract(bot: Bot, event: MessageEvent, state: T_State):
    message = str(event.message).strip()
    bvids = re.findall(r"(^BV[a-zA-Z0-9]{10})", message, flags=re.I)
    for i in bvids:
        resp = await Extract.av_parse(bvid2aid(i))
        await bot.send(event=event, message=Message(resp))


av_extract = on_regex(r"^av\d+", flags=re.I)


@av_extract.handle()
async def _av_extract(bot: Bot, event: MessageEvent, state: T_State):
    message = str(event.message).strip()
    aids = re.findall(r"^av(\d+)", message, flags=re.I)
    for i in aids:
        resp = await Extract.av_parse(int(i))
        await bot.send(event=event, message=Message(resp))


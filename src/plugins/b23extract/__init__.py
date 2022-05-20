import re
from typing import Callable

import aiohttp
from bilibili_api import exceptions, Credential
from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent
from nonebot.log import logger
from nonebot.plugin import require

from src.utils.config import B23Config
from .data_source import Extract

# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

register("b23extract", "B站分享解析")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag

'''
本插件大量代码借(chao)鉴(xi)了 https://github.com/mengshouer/nonebot_plugin_analysis_bilibili
PS:这个项目有点迷，没有LICENSE文件，但是readme中有`license MIT`的badge……姑且认为作者按MIT协议开源吧
'''

# 接入帮助系统
__usage__ = '视频/专栏/直播信息获取：直接发送分享链接/AV/BV号/小程序分享即可'

__help_version__ = '0.2.0 (Flandre)'

__help_plugin_name__ = 'B站解析'

credential = Credential(sessdata=B23Config.sessdata, bili_jct=B23Config.bili_jct, buvid3=B23Config.buvid3)

b23_extract = on_regex(r"(b23.tv)|(bili(22|23|33|2233).cn)|(live.bilibili.com)|(bilibili.com/(video|read|bangumi))|("
                       r"(av|cv)(\d+))|(BV([a-zA-Z0-9]{10})+)|(\[\[QQ小程序\]哔哩哔哩\])|(QQ小程序&amp;#93;哔哩哔哩)|("
                       r"QQ小程序&#93;哔哩哔哩)", flags=re.I, rule=online("b23extract") & gag())


@b23_extract.handle()
async def _b23_extract(bot: Bot, event: MessageEvent):
    message = str(event.message).strip()
    short_url = re.findall(r"((b23.tv|(bili(22|23|33|2233).cn))(\\?)/[A-Za-z\d]+)", message)
    try:
        if short_url:
            url = "https://" + short_url[0][0].replace("\\", "")
            async with aiohttp.ClientSession() as session:
                server_resp = await session.get(url, timeout=1000)
                real_url = str(server_resp.url)
            if real_url:
                extract = Extract(real_url, credential=credential, proxy=B23Config.proxy, use_image=B23Config.use_image)
                resp = await extract.process()
            else:
                resp = "获取稿件信息失败：无法解析该短链"
        else:
            extract = Extract(message, credential=credential, proxy=B23Config.proxy, use_image=B23Config.use_image)
            resp = await extract.process()
    except exceptions.ResponseCodeException as e:
        logger.info(e)
        resp = str(e)
    except exceptions.NetworkException as e:
        logger.error(e)
        resp = "获取稿件信息失败：网络错误"
    except Exception as e:
        logger.error(e)
        resp = "获取稿件信息失败：未知错误"

    if resp:
        if isinstance(resp, tuple):
            for i in resp:
                await bot.send(event=event, message=Message(i))
        else:
            await bot.send(event=event, message=Message(resp))

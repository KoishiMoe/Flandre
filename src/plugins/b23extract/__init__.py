import re

import aiohttp
from bilibili_api import exceptions, Credential
from nonebot import on_regex
from nonebot.adapters.cqhttp import Bot, Message, MessageEvent, unescape
from nonebot.typing import T_State
from nonebot.log import logger

from src.utils.config import b23Config
from .data_source import Extract

'''
本插件大量代码借(chao)鉴(xi)了 https://github.com/mengshouer/nonebot_plugin_analysis_bilibili （该项目readme指出其以MIT协议开源）
'''

credential = Credential(sessdata=b23Config.sessdata, bili_jct=b23Config.bili_jct, buvid3=b23Config.buvid3)

b23_extract = on_regex(r"(b23.tv)|(bili(22|23|33|2233).cn)|(live.bilibili.com)|(bilibili.com/(video|read|bangumi))|("
                       r"^(av|cv)(\d+))|(^BV([a-zA-Z0-9]{10})+)|(\[\[QQ小程序\]哔哩哔哩\])|(QQ小程序&amp;#93;哔哩哔哩)|("
                       r"QQ小程序&#93;哔哩哔哩)", flags=re.I)


@b23_extract.handle()
async def _b23_extract(bot: Bot, event: MessageEvent, state: T_State):
    message = str(event.message).strip()
    short_url = re.findall(r"((http(s?):(\\?)/(\\?)/b23.tv|(bili(22|23|33|2233).cn))(\\?)/[A-Za-z0-9]+)", message)
    try:
        if short_url:
            url = short_url[0][0].replace("\\", "")
            async with aiohttp.ClientSession() as session:
                server_resp = await session.get(url, timeout=1000)
                real_url = str(server_resp.url)
            if real_url:
                extract = Extract(real_url, credential=credential, proxy=b23Config.proxy)
                resp = await extract.pre_process()
            else:
                resp = "获取稿件信息失败：无法解析该短链"
        else:
            extract = Extract(message, credential=credential, proxy=b23Config.proxy)
            resp = await extract.pre_process()
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
        await bot.send(event=event, message=Message(resp))



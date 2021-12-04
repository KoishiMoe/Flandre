import re
import json

from json import JSONDecodeError

from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Bot, MessageEvent, unescape
from nonebot import on_regex

from src.utils.config import AntiMiniapp

# 接入帮助系统
__usage__ = '直接发送小程序即可，注意部分小程序无法被转换为外链（常见于游戏类小程序）'

__help_version__ = '0.1.0 (Flandre)'

__help_plugin_name__ = '小程序解析'


anti_miniapp = on_regex('com.tencent.miniapp')


@anti_miniapp.handle()
async def _anti_miniapp(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.message).strip()
    for keyword in AntiMiniapp.ignored_keywords:
        if re.search(keyword, msg, re.I):
            # 忽略指定的关键字
            return
    try:
        msg = re.findall(r"\{.*(?=\})\}", msg)[0]
        msg = unescape(msg)
        data: dict = json.loads(msg)
        url = data.get("meta", None).get("detail_1", None).get("qqdocurl", None)
        # 因为url键对应的链接只能打开小程序，所以提取qqdocurl作为小程序链接
        if url:
            await bot.send(event, message=url)
        else:
            raise AttributeError  # 偷懒共用下AttributeError的错误提示23333
    except KeyError as e:
        await bot.send(event, message="解析失败：不是合法的小程序")
    except JSONDecodeError as e:
        await bot.send(event, message="解析失败：无法找到有效的json字段")
    except AttributeError as e:
        await bot.send(event, message="解析失败：无法找到有效的链接")


anti_structmsg = on_regex('com.tencent.structmsg')


@anti_structmsg.handle()
async def _anti_structmsg(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.message).strip()
    for keyword in AntiMiniapp.ignored_keywords:
        if re.search(keyword, msg, re.I):
            # 忽略指定的关键字
            return
    try:
        msg = re.findall(r"\{.*(?=\})\}", msg)[0]
        msg = unescape(msg)
        data: dict = json.loads(msg)
        meta = data.get("meta", None)
        data2 = meta.get(list(meta.keys())[0], None)
        url = data2.get("jumpUrl", None)
        # 目前样本比较少，不确定jumpUrl是不是一定是跳转链接，如有问题请提issue
        if url:
            await bot.send(event, message=url)
        else:
            raise AttributeError  # 偷懒共用下AttributeError的错误提示23333
    except KeyError as e:
        await bot.send(event, message="解析失败：不是合法的小程序")
    except JSONDecodeError as e:
        await bot.send(event, message="解析失败：无法找到有效的json字段")
    except AttributeError as e:
        await bot.send(event, message="解析失败：无法找到有效的链接")

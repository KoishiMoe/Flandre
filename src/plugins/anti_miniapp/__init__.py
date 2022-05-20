import json
import re

import defusedxml.ElementTree as ElementTree
from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, unescape, MessageSegment
from nonebot.log import logger
from nonebot.plugin import require

from src.utils.config import AntiMiniapp

JSONDecodeError = json.JSONDecodeError

# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

register("anti_miniapp", "小程序解析")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag

# 接入帮助系统
__usage__ = '直接发送小程序即可，注意部分小程序无法被转换为外链（常见于游戏类小程序）'

__help_version__ = '0.3.2 (Flandre)'

__help_plugin_name__ = '小程序解析'

anti_miniapp = on_regex('com.tencent.miniapp', rule=online("anti_miniapp") & gag())


@anti_miniapp.handle()
async def _anti_miniapp(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()
    for keyword in AntiMiniapp.ignored_keywords:
        if re.search(keyword, msg, re.I):
            # 忽略指定的关键字
            return
    try:
        msg = re.findall(r"{.*(?=})}", msg)[0]
        msg = unescape(msg)
        data: dict = json.loads(msg)
        url = data.get("meta", None).get("detail_1", None).get("qqdocurl", None)
        # 因为url键对应的链接只能打开小程序，所以提取qqdocurl作为小程序链接
        if url:
            await bot.send(event, message=url)
        else:
            raise AttributeError  # 偷懒共用下AttributeError的错误提示23333
    except KeyError:
        await bot.send(event, message="解析失败：不是合法的小程序")
    except JSONDecodeError:
        await bot.send(event, message="解析失败：无法找到有效的json字段")
    except AttributeError:
        await bot.send(event, message="解析失败：无法找到有效的链接")


anti_structmsg = on_regex('com.tencent.structmsg', rule=online("anti_miniapp") & gag())


@anti_structmsg.handle()
async def _anti_structmsg(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()
    for keyword in AntiMiniapp.ignored_keywords:
        if re.search(keyword, msg, re.I):
            # 忽略指定的关键字
            return
    try:
        msg = re.findall(r"{.*(?=})}", msg)[0]
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
    except KeyError:
        await bot.send(event, message="解析失败：不是合法的小程序")
    except JSONDecodeError:
        await bot.send(event, message="解析失败：无法找到有效的json字段")
    except AttributeError:
        await bot.send(event, message="解析失败：无法找到有效的链接")


anti_xml = on_regex(r'\[CQ:xml', rule=online("anti_miniapp") & gag())


@anti_xml.handle()
async def _anti_xml(bot: Bot, event: MessageEvent):
    msg = str(event.raw_message).strip()
    msg_id = event.message_id
    url = ''
    for keyword in AntiMiniapp.ignored_keywords:
        if re.search(keyword, msg, re.I):
            # 忽略指定的关键字
            return

    xml_data = str(re.findall(r'data=(.+</msg>)', msg, flags=re.DOTALL)[0])
    if xml_data:
        tree = ElementTree.fromstring(xml_data)
        try:
            root = tree.getroot()
            if 'url' in root.attrib and isinstance(root.attrib, dict):
                url = root.attrib.get('url', '')
            else:
                for child in tree:
                    if 'url' in child.attrib and isinstance(child.attrib, dict):
                        url = child.attrib.get('url', '')
                        break
        except AttributeError:
            # 腾讯自家的一些xml结构比较特殊（例如好友推荐、加群邀请），只有一个元素
            if 'url' in tree.attrib and isinstance(tree.attrib, dict):
                url = tree.attrib.get('url', '')
        except Exception as e:
            logger.warning(f"尝试解析xml消息时出现了未知错误：{e}")

    if url:
        url = unescape(url)
        await bot.send(event=event, message=MessageSegment.reply(msg_id) + url)

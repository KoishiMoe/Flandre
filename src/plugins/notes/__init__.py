import re
from random import shuffle

from jieba import lcut
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.matcher import Matcher
from nonebot.plugin import require

from . import sqlite, config_manager
from .config import get_notes, NoteMatcher

# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

register("notes", "便签")

# 接入频率限制
require("ratelimit")
from ..ratelimit.config_manager import register as register_ratelimit
from ..ratelimit.rule import limit

register_ratelimit("notes", "便签")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag

# 接入帮助系统
__usage__ = '本功能用于让bot能够快速回复一些FAQ，例如下载地址、群规之类；无在线词库\n' \
            '添加：添加便签 [-t 类型] [-c 关键词或表达式] [-r 回复内容] [-g] [-group 群号] [-a]\n' \
            '   其中所有参数均为可选参数，如果不提供，bot会使用默认值或者询问。各参数详细信息：\n' \
            '   -t 类型，有 1.关键词 2.全文 3.正则\n' \
            '   -c 要用来匹配的关键词/文字或正则表达式。如果是正则表达式，推荐不要用参数形式提供，否则可能被错误切割\n' \
            '   -r 回复的内容，只支持纯文本，不要发送图片、表情之类\n' \
            '   -g 若添加该参数，表示操作全局便签（仅超管有权限）\n' \
            '   -group 若添加该参数，表示操作指定群的便签（仅超管）\n' \
            '   -a 若添加该参数，表示需要 @bot 才能生效\n' \
            '删除： 删除便签 便签id [-g] [-group 群号]\n' \
            '   便签id必须提供，具体的值可以用下面提到的命令查询。注意各群之间、群与全局间的id均是独立的。其他参数的作用与权限同上\n' \
            '屏蔽/解除屏蔽：屏蔽便签/解除屏蔽便签 便签id [-group 群号]\n' \
            '   屏蔽的作用：如果某个全局便签的内容不适合在特定群出现，群管可以在本群屏蔽该便签，因此只能用于群内屏蔽全局便签；如果要屏蔽群内便签或全局屏蔽某全局便签，请直接删除它\n' \
            '查询便签：查询便签 [-g] [-group 群号]\n' \
            '   群内默认显示本群的便签，私聊默认显示全局。参数的作用同上，但权限有一点不同：所有人都可以查询全局便签'

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = '便签'

notes = on_message(rule=limit("notes") & gag() & online("notes"), priority=10, block=False)


@notes.handle()
async def _notes(bot: Bot, event: MessageEvent, matcher: Matcher):
    gid = event.group_id if isinstance(event, GroupMessageEvent) else 0
    matchers = await get_notes(gid)
    if matchers:
        matched = match_msg(str(event.message).strip(), matchers, event.to_me)
        if matched:
            matcher.stop_propagation()
            await notes.finish(matched.resp)


def match_msg(message: str, matchers: list[NoteMatcher], at: bool) -> NoteMatcher:
    words = []
    for matcher in matchers:
        if matcher.at and not at:
            continue
        match matcher.type:
            case "regex":
                if re.findall(matcher.content, message, flags=re.I):
                    return matcher
            case "full":
                if matcher.content == message:
                    return matcher
            case "kwd":
                if not words:  # 放在这里切是防止没有关键词类型的matcher时也进行分词
                    words = lcut(message, cut_all=False)
                    shuffle(words)
                if matcher.content in words:
                    return matcher
    for matcher in matchers:
        if matcher.at and not at:
            continue
        if matcher.type == "kwd" and matcher.content in message:
            return matcher

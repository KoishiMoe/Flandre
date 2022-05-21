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
__usage__ = ''

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = 'notes'

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

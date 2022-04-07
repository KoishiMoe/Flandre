from random import randint

from nonebot.adapters.onebot.v11 import MessageEvent, PrivateMessageEvent, GroupMessageEvent

from .file_loader import get_full_wordbank
from .exceptions import UnknownMatcherTypeError
from .matcher import *


async def get_matcher(event: MessageEvent) -> dict | None:
    # 这里本来打算写成nonebot标准的rule的，不过又想到匹配之后的具体结果没处传……
    message = str(event.message).strip()
    if isinstance(event, GroupMessageEvent):
        bank = await __load_data(event.group_id)
    elif isinstance(event, PrivateMessageEvent):
        bank = await __load_data(0)
    else:
        return None

    matcher: dict
    for matcher in bank:
        matcher_config: dict = matcher["matcher"]
        if matcher_config.get("atme", True) and not event.to_me:
            continue
        if randint(1, 100) <= matcher_config.get("probability", 100):
            match = await __build_matcher(matcher_config)
            if match.match(message):
                return matcher

    return None


async def __load_data(gid: int):
    bank = await get_full_wordbank(gid)
    bank = await __build_sorted_dict(bank)
    return bank


async def __build_sorted_dict(bank: list) -> list:
    return sorted(bank, key=lambda i: i["matcher"].get("priority", 10), reverse=True)


async def __build_matcher(matcher: dict) -> Matcher:
    probability: int = matcher.get("probability", 100)
    priority: int = matcher.get("priority", 10)
    atme: bool = matcher.get("atme", True)
    match matcher["type"]:
        case "prefix":
            return PrefixMatcher(matcher["keyword"], probability, priority, atme)
        case "keyword":
            return KeywordMatcher(matcher["keyword"], matcher.get("simple_mode", False), probability, priority, atme)
        case "full":
            return FullTextMatcher(matcher["text"], probability, priority, atme)
        case "regex":
            return RegexMatcher(matcher["regex"], matcher.get("ignore_case", True), probability, priority, atme)
        case _:
            raise UnknownMatcherTypeError(f"Unknown matcher type {matcher['type']}")

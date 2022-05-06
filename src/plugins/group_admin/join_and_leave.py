import re
from typing import Callable

from nonebot import on_request, logger, on_notice
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupRequestEvent, GroupIncreaseNoticeEvent, GroupDecreaseNoticeEvent
from nonebot.matcher import Matcher
from nonebot.plugin import require

from .ban import check_ban
from .utils import get_group_config
from .whitelist import check_trust

# 接入禁言检查
gag: Callable = require("utils").not_gagged

# 接入服务管理器
register: Callable = require("service").register
online: Callable = require("service").online

register("welcome", "入群欢迎")

group_join_request = on_request(block=False)


@group_join_request.handle()
async def _check_join(bot: Bot, event: GroupRequestEvent, matcher: Matcher):
    if event.sub_type == "invite":
        return
    else:
        matcher.stop_propagation()

    if await check_trust(event.group_id, event.user_id):
        await bot.set_group_add_request(flag=event.flag, sub_type=event.sub_type, approve=True)
        logger.info(f"由于用户在白名单内，已同意{event.user_id}加入群{event.group_id}")
    elif await check_ban(event.group_id, event.user_id):
        await bot.set_group_add_request(flag=event.flag, sub_type=event.sub_type, approve=False, reason="用户已被封禁")
        logger.info(f"由于用户已被封禁，已拒绝{event.user_id}加入群{event.group_id}")
    else:
        answer = event.comment
        group_config = await get_group_config(event.group_id)
        pattern = group_config["autoAgreePattern"]
        if pattern and pattern != "#" and re.match(pattern, answer, flags=re.I):
            await bot.set_group_add_request(flag=event.flag, sub_type=event.sub_type, approve=True)
            logger.info(f"按照匹配规则，已同意{event.user_id}加入群{event.group_id}")


group_welcome = on_notice(rule=online("welcome") & gag(), block=False)


@group_welcome.handle()
async def _welcome(bot: Bot, event: GroupIncreaseNoticeEvent, matcher: Matcher):
    if event.user_id == event.self_id:
        return
    else:
        matcher.stop_propagation()

    group_config = await get_group_config(event.group_id)
    welcome = group_config["welcome"]
    if welcome and welcome != "#":
        try:
            user_info = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
            username = user_info.get("card") or user_info.get("nickname")
        except Exception as e:
            logger.warning(f"获取群{event.group_id}的成员{event.user_id}的信息时发生了错误：{e}")
            username = ""
        welcome = welcome.replace("#userid", str(event.user_id)).replace("#username", str(username))
        await group_welcome.finish(MessageSegment.at(event.user_id) + welcome)


group_leave = on_notice(rule=online("welcome") & gag(), block=False)


@group_leave.handle()
async def _leave(bot: Bot, event: GroupDecreaseNoticeEvent, matcher: Matcher):
    if event.user_id == event.self_id:
        return
    else:
        matcher.stop_propagation()

    group_config = await get_group_config(event.group_id)
    leave = group_config["leave"]
    if leave and leave != "#":
        try:
            user_info = await bot.get_stranger_info(user_id=event.user_id)
            nickname = user_info.get("nickname")
        except Exception as e:
            logger.warning(f"获取用户{event.user_id}的信息时发生了错误：{e}")
            nickname = ""

        notice = leave.replace("#userid", str(event.user_id)).replace("#username", str(nickname))
        await group_welcome.finish(notice)

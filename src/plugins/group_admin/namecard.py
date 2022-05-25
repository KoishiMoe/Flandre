import re

from nonebot import on_command, on_message, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.plugin import require
from nonebot.rule import Rule, to_me
from nonebot.typing import T_State

from src.utils.command_processor import process_command
from src.utils.str2img import Str2Img
from .ban_and_whitelist import check_trust
from .utils import get_global_group, get_group_config, get_groups_in_global_group, is_group_admin

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag

# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

register("namecard", "群名片自动检查")


def _namecard_warning_rule() -> Rule:
    async def _check(bot: Bot, event: GroupMessageEvent) -> bool:
        return await _check_namecard(bot, event.group_id, event.user_id)
        # 要不要no_cache?感觉每条消息都刷新的话有点难顶……如果真的妨碍了使用的话请提issue吧……

    return Rule(_check)


namecard_auto_check = on_message(rule=online("namecard") & gag() & _namecard_warning_rule(), block=False)


@namecard_auto_check.handle()
async def _namecard_check(bot: Bot, event: GroupMessageEvent):
    await namecard_auto_check.finish(MessageSegment.at(event.user_id) +
                                     "你的群名片似乎不符合本群的规则的说～请及时修改╮（╯＿╰）╭")


namecard_manual_check = on_command("checknamecard", aliases={"检测群名片", "检查群名片"},
                                   rule=gag() & to_me() & online("group_admin"),
                                   permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@namecard_manual_check.handle()
async def _namecard_check(bot: Bot, event: GroupMessageEvent, state: T_State, raw_command: str = RawCommand()):
    msg = str(event.message)
    param_list, param_dict = process_command(raw_command, msg)
    if param_dict.get("g"):
        global_group = await get_global_group(event.group_id)
        if not global_group:
            await namecard_manual_check.finish("啊，这个群似乎还没有加入群组的说……")
        groups = await get_groups_in_global_group(global_group)
    else:
        groups = {event.group_id}

    if param_dict.get("k"):
        if param_dict["k"] in (True, "True", "true", "T", "t"):
            state["kick"] = True
        else:
            state["kick"] = False
    else:
        state["kick"] = False

    result = {}
    for group in groups:
        member_list = await bot.get_group_member_list(group_id=group)
        group_config = await get_group_config(group)
        pattern = group_config.get("nameCardPattern")
        if pattern and pattern != "#":
            pattern = re.compile(pattern, flags=re.I)
            for member in member_list:
                member_id = member.get("user_id")
                if not pattern.fullmatch(member.get("card") or member.get("nickname")):
                    if await _check_namecard(bot, group, member_id, no_cache=True, ignore_prompt=True):
                        # 有时候名片没刷新过来，此外白名单用户不必检测
                        if result.get(group):
                            result[group][member.get("user_id", 0)] = member.get("card") or member.get("nickname")
                        else:
                            result[group] = {member.get("user_id", 0): member.get("card") or member.get("nickname")}

    output = ""
    for group in result.keys():
        output += f"群{group}中名片不合规的成员有：\n"
        for k, v in result[group].items():
            output += f"    {k}：{v}\n"
    if len(output) > 200:
        output = Str2Img().gen_message(output)

    if not output:
        output = "未检测到群名片不合规的成员"

    if not state["kick"]:
        await namecard_manual_check.finish(output)
    else:
        await bot.send(event, output)
        state["result"] = result


@namecard_manual_check.got("sure_kick", "你确定要踢出这些群名片不合规的成员吗？操作不可逆！（y/N)")
async def _sure_kick(bot: Bot, event: GroupMessageEvent, state: T_State):
    sure = str(state["sure_kick"]).strip() in ("y", "Y", "t", "T", "true", "True", "是", "确定")
    if not sure:
        await namecard_manual_check.finish("已取消")

    name_list = state["result"]

    result = {}

    for group in name_list.keys():
        if await is_group_admin(group, int(bot.self_id)):
            for k, v in name_list[group].items():
                try:
                    await bot.set_group_kick(group_id=group, user_id=k)
                except Exception as e:
                    logger.warning(f"从群{group}踢出{k}时发生了错误：{e}")
                    if result.get(group):
                        result[group][k] = [v]
                    else:
                        result[group] = {k: v}
        else:
            result[group] = {"*", "*"}

    if result:
        output = "操作完成，但踢出下列用户时发生了错误：\n"
        for group in result:
            output += f"群{group}：\n"
            for k, v in result[group].items():
                output += f"    {k}: {v}\n"
    else:
        output = "操作完成，没有错误发生"

    if len(output) > 200:
        output = Str2Img().gen_message(output)

    await namecard_manual_check.finish(output)


async def _check_namecard(bot: Bot, gid: int, uid: int, no_cache: bool = False, ignore_prompt: bool = False) -> bool:
    """检查名片是否合规，合规返回False"""
    group_config = await get_group_config(gid)
    pattern = group_config.get("nameCardPattern")
    prompt = group_config.get("illegalNameCardPrompt")
    if not ignore_prompt and not prompt:
        # 不忽略提醒设置，但是提醒关闭，则直接返回合规（用于rule）
        return False
    if not pattern or pattern == "#":
        return False

    if await check_trust(gid, uid):
        return False
    try:
        member_info = await bot.get_group_member_info(group_id=gid, user_id=uid, no_cache=no_cache)
        card = member_info.get("card") or member_info.get("nickname")
        return not bool(re.fullmatch(pattern, card, flags=re.I))
    except Exception as e:
        logger.warning(f"获取群{gid}成员{uid}的信息时发生了错误：{e}")
    return False

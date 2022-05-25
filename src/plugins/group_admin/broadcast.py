import asyncio

from nonebot import on_command, logger, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from src.utils.command_processor import process_command
from .utils import get_global_group, get_groups_in_global_group


# 接入服务管理器
require("service")
from ..service.rule import online

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag


broadcast = on_command("broadcast", aliases={"广播"}, rule=online("group_admin") & gag(),
                       permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, state={"global": False})
global_broadcast = on_command("globalbroadcast", aliases={"全局广播"}, permission=SUPERUSER, state={"global": True})


@broadcast.handle()
@global_broadcast.handle()
async def _broadcast(bot: Bot, event: MessageEvent, state: T_State, raw_command: str = RawCommand()):
    param_list, param_dict = process_command(raw_command, str(event.message))

    if not state["global"] and isinstance(event, GroupMessageEvent):
        global_group = await get_global_group(event.group_id)
        if not global_group:
            await broadcast.finish("广播失败：这个群似乎没有加入群组的说……")
        state["groups"] = await get_groups_in_global_group(global_group)
    elif state["global"]:
        groups = await bot.get_group_list()
        state["groups"] = [group.get("group_id") for group in groups]
    else:
        # 超管私聊，允许指定群号
        group = param_dict.get("g")
        if not group or not isinstance(group, str):
            await broadcast.finish("未提供要广播的群号或群号不合法，请使用-g参数提供合法的群号/群组")
        if group.isdigit():
            global_group = await get_global_group(param_dict.get(group))
            if not global_group:
                await broadcast.finish("广播失败：这个群似乎没有加入群组的说……")
        else:
            global_group = group

        groups = await get_groups_in_global_group(global_group)
        state["groups"] = groups

    if param_dict.get("a"):
        state["at_all"] = True
    if param_dict.get("n"):
        state["notice"] = True

    if param_list:
        state["message"] = ' '.join(param_list)


@broadcast.got("message", "请发送你要广播的内容～")
async def _broadcast_send(bot: Bot, event: MessageEvent, state: T_State):
    message = str(state["message"]).strip()
    at_all = bool(state.get("at_all"))
    notice = bool(state.get("notice"))

    fail = []

    for group in state["groups"]:
        if not notice:
            try:
                if at_all:
                    at_all_remain = await bot.call_api("get_group_at_all_remain", group_id=group)
                    can_at_all = at_all_remain.get("can_at_all")
                    if can_at_all:
                        msg = MessageSegment.at("all") + message
                    else:
                        msg = message
                else:
                    msg = message
                await bot.send_group_msg(group_id=group, message=msg, auto_escape=True)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"向群{group}发送消息{message}时发生了错误：{e}")
                fail.append(str(group))  # 不转成str的话没法join
        else:
            try:
                await bot.call_api("_send_group_notice", group_id=group, content=message)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"向群{group}发送公告{message}出现了错误：{e}")
                fail.append(str(group))

    output = "操作完成，"
    if fail:
        output += f"有{len(fail)}个群广播失败, 分别为{'、'.join(fail)}"
    else:
        output += "已成功向群组中所有群广播"

    await broadcast.finish(output)

from typing import Callable

from nonebot import on_command, require
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER

from src.utils.command_processor import process_command
from .config import modify_config, get_config
from .rule import check_limit, services, register

# 接入禁言检查
gag: Callable = require("utils").not_gagged

# 接入频率限制
register("ratelimit", "限制普通用户查询频率限制的频率")

modify = on_command("设置频率", aliases={"设置频率限制", "修改频率", "修改频率限制", "频率设置"},
                    permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@modify.handle()
async def _modify(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    param_list, param_dict = process_command(raw_command, str(event.message))

    # 群聊中，不加参数默认被视为设置本群的限制，超管可以加参数-global设置全局，-g (-g 0)设置群全局，-u设置用户
    # 私聊中，默认设置用户，-g 群号 设置指定群，其他同上
    no_param = True
    gid = None
    is_daily = bool(param_dict.get("d"))
    glob, group, user = param_dict.get("global"), param_dict.get("g"), param_dict.get("u")
    if glob or group or user:
        if not await SUPERUSER(bot, event):
            await modify.finish("抱歉，你没有权限进行该操作")
        else:
            no_param = False
    if no_param:
        if isinstance(event, GroupMessageEvent):
            limit_type = 2
            gid = event.group_id
        else:
            limit_type = 3

    if glob:
        limit_type = 1
    elif group:
        limit_type = 2
        if isinstance(group, str) and not group.isdigit():
            await modify.finish("抱歉，你提供的群号似乎不太对……")
        gid = 0 if isinstance(group, bool) else int(group)
    elif user:
        limit_type = 3

    if len(param_list) < 2:
        await modify.finish("啊，你似乎忘了提供要限制的服务和值了……")
    elif not (param_list[1].isdigit() and 0 <= int(param_list[1]) <= 100):
        await modify.finish("啊……你提供的限制的值似乎不太对……它应该是个非负整数的说……")
    else:
        service = param_list[0]
        if service not in services.keys():
            await modify.finish("啊……你提供的服务似乎并没有被注册的说……要不检查下是不是拼写错误？")
        value = int(param_list[1])

    modify_config(value=value, service=service, limit_type=limit_type, daily=is_daily, gid=gid)
    await modify.finish("操作完成！")


query = on_command("查询频率", aliases={"查询频率限制", "频率查询"}, rule=gag())


@query.handle()
async def _query(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    if not await check_limit(bot, event, "ratelimit", False):
        await query.finish("啊，你查的太快了……")
    msg = str(event.message).strip().removeprefix(raw_command).strip()
    if msg:
        if not await SUPERUSER(bot, event):
            await query.finish("抱歉，你没有权限查询指定群的限制")
        if not msg.isdigit():
            await query.finish("啊，你提供的群号似乎不太对的样子……")
        else:
            gid = int(msg)
    elif isinstance(event, GroupMessageEvent):
        gid = event.group_id
    else:
        gid = 0

    output = ""
    for k, v in services.items():
        output += f"{k}：{v}\n" \
                  f"    全局： {get_config(k, 1, False)}(cd)/{get_config(k, 1, True)}(每日)\n"
        if gid:
            output += f"    本群： {get_config(k, 2, False, gid)}(cd)/{get_config(k, 2, True, gid)}(每日)\n"
        output += f"    群全局：{get_config(k, 2, False, 0)}(cd)/{get_config(k, 2, True, 0)}(每日)\n" \
                  f"    用户：{get_config(k, 3, False)}(cd)/{get_config(k, 3, True)}(每日)\n"

    await check_limit(bot, event, "ratelimit", True)
    await query.finish(output)

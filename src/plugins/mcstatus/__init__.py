import re
from typing import Callable

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.params import RawCommand
from nonebot.plugin import require

from . import config_manager
from .config import Config
from .utils import get_server_status

# 接入服务管理器
register: Callable = require("service").register
online: Callable = require("service").online

register("mcstatus", "mc服务器状态")

# 接入禁言检查
gag: Callable = require("utils").not_gagged

# 接入帮助系统
__usage__ = ''

# 接入频率限制
register_ratelimit: Callable = require("ratelimit").register
check_limit: Callable = require("ratelimit").check_limit

register_ratelimit("mcstatus", "mc服务器状态")

mcping = on_command("mcping", aliases={"mcstatus", "服务器状态"}, rule=online("mcstatus") & gag())


@mcping.handle()
async def _mcping(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    if not await check_limit(bot, event, "mcstatus", False):
        await mcping.finish("让服务器君休息一下吧～")
    server = str(event.message).strip().removeprefix(raw_command).strip()
    if not server:
        if not isinstance(event, GroupMessageEvent):
            await mcping.finish("请提供有效的服务器地址！")
        else:
            # 群聊尝试获取本群默认
            cfg = Config(event.group_id)
            srv = cfg.get_server()
            if not srv:
                await mcping.finish("你群似乎还没有绑定默认服务器……")
            address, port, is_be = srv.values()
    else:
        params = server.split()
        if len(params) == 1:  # 只提供了名称或ip
            if isinstance(event, GroupMessageEvent):  # 群聊中先尝试名称
                cfg = Config(event.group_id)
                srv = cfg.get_server(params[0])
                if srv:
                    address, port, is_be = srv.values()
            if "address" not in locals():  # 如果没获取到名称或者是私聊，当作ip处理
                address_and_port = re.split("[:：]", params[0][::-1], maxsplit=1)  # 只切一次，防ipv6
                address_and_port = [i[::-1] for i in address_and_port[::-1]]
                if len(address_and_port) >= 2:  # 切出来有两份，则后者应该是端口号
                    if not address_and_port[1].isdigit():
                        await mcping.finish("你提供的端口号似乎不是数字……")
                    address, port, is_be = address_and_port[0], int(address_and_port[1]), None
                else:
                    address, port, is_be = params[0], 0, None
        else:  # 因为排除过为空，此处认为>=2，即地址+是否是be
            address_and_port = re.split("[:：]", params[0][::-1], maxsplit=1)
            address_and_port = [i[::-1] for i in address_and_port[::-1]]
            if len(address_and_port) >= 2:  # 同样，后者视为端口号
                if not address_and_port[1].isdigit():
                    await mcping.finish("你提供的端口号似乎不是数字……")
                address, port = address_and_port[0], int(address_and_port[1])
            else:
                address, port = params[0], 0
            is_be = params[1] in ("pe", "bedrock", "b", "B", "be", "BE", "PE", "Bedrock")

    output = await get_server_status(address, port, is_be)
    await check_limit(bot, event, "mcstatus", True)
    await mcping.finish(output)

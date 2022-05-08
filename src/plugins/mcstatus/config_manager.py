import re
from typing import Callable

from nonebot import on_command, require
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from src.utils.command_processor import process_command
from src.utils.str2img import Str2Img
from .config import Config
from .utils import je_or_be

# 接入服务管理器
online: Callable = require("service").online

# 接入频率限制
limit: Callable = require("ratelimit").limit

# 接入禁言检查
gag: Callable = require("utils").not_gagged

server_manage = on_command("mc", aliases={"minecraft"}, rule=to_me() & online("mcstatus") & gag() & limit("ratelimit"),
                           permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@server_manage.handle()
async def _server_manager(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    param_list, param_dict = process_command(raw_command, str(event.message))

    if param_dict.get("g"):
        if not await SUPERUSER(bot, event):
            await server_manage.finish("抱歉，你没有权限为指定群绑定/解绑服务器")
        if not param_dict["g"].isdigit():
            await server_manage.finish("啊，提供的群号似乎不太对……")
        gid = int(param_dict["g"])
    else:
        if not isinstance(event, GroupMessageEvent):
            await server_manage.finish("啊，你似乎忘了写群号……")
        else:
            gid = event.group_id

    if not param_list:
        await server_manage.finish("啊，你似乎忘了提供参数（操作、服务器名称、地址）")

    add = param_list[0] in ("add", "join", "new", "添加", "bind", "绑定")
    default = param_list[0] in ("default", "默认", "设置默认")
    if not add and not default and param_list[0] not in ("remove", "del", "delete", "解绑", "删除"):
        await server_manage.finish("操作无效！有效的操作有：添加(add/添加/绑定)、删除(remove/解绑/删除)和设置默认（default/默认/设置默认）")

    if (add and len(param_list) < 3) or (not add and len(param_list) < 2):
        await server_manage.finish("啊，似乎缺少了一些参数……最少需要提供的参数有：\n"
                                   "添加：操作名称(add/添加) 服务器名称 服务器地址\n"
                                   "删除/设置默认：操作名称(del/删除/default/默认) 服务器名称")

    name = param_list[1]
    if add:
        address = re.split("[:：]", param_list[2])
        if len(address) == 1:
            port = 0
        elif not address[1].isdigit():
            await server_manage.finish("你提供的端口号似乎不是数字……要不检查一下看看？")
        else:
            port = int(address[1])
        host = address[0]

        if len(param_list) >= 3:
            is_je = not param_list[2] in ("pe", "bedrock", "b", "B", "be", "BE", "PE", "Bedrock")
        else:
            is_je = await je_or_be(host, port)
            if is_je is None:
                await server_manage.finish("呜……检测不到你的服务器类型……也许服务器宕机了，或者是服主屏蔽了我的ip，"
                                           "抑或这是个不受支持的服务端……也许可以试试在服务器地址后手动指定服务器类型（je/be）")

    config = Config(gid)
    if add:
        if config.add_server(name, host, port, not is_je):
            await server_manage.finish(f"添加服务器 {name} 成功！")
        else:
            await server_manage.finish(f"添加服务器 {name} 失败，名称可能已经被占用")
    elif default:
        if config.set_default(name):
            await server_manage.finish(f"成功将 {name} 设为默认服务器")
        else:
            await server_manage.finish(f"错误：服务器 {name} 不存在")
    else:
        if config.del_server(name):
            await server_manage.finish(f"删除服务器 {name} 成功！")
        else:
            await server_manage.finish(f"删除服务器 {name} 失败，请检查名称是否有误")


list_server = on_command("mclist", aliases={"服务器列表"}, rule=online("mcstatus") & gag() & limit("mcstatus"))


async def _list_server(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    msg = str(event.message).strip().removeprefix(raw_command).strip()
    if not await SUPERUSER(bot, event):
        await list_server.finish("抱歉，你没有权限查看其他群的服务器列表")
    if not isinstance(event, GroupMessageEvent) and not msg:
        await list_server.finish("啊，你似乎忘了提供群号诶……")
    if msg and not msg.isdigit():
        await list_server.finish("啊，你提供的群号似乎不太对的样子……")

    if msg:
        gid = int(msg)
    else:
        gid = event.group_id

    config = Config(gid)
    ls = config.list_data()
    if len(ls) > 200:
        img = Str2Img().gen_bytes(ls)
        ls = MessageSegment.image(img)
    await list_server.finish(ls)

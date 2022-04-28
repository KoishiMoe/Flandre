from io import BytesIO

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.log import logger
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.plugin import export

from src.utils.command_processor import process_command
from src.utils.str2img import Str2Img
from .query import get_status, update_status

services = {}


@export()
def register(service: str, description: str = ""):
    if services.get(service):
        logger.warning(f"服务管理器：有多个插件注册了同一服务名称：{service}，这可能导致服务管理出现异常，请排查是否安装了冲突的插件")
    services[service] = description


ls = on_command("services", aliases={"service", "srv"})


@ls.handle()
async def _ls(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    param_list, param_dict = process_command(raw_command, str(event.message))
    output = ""

    async def _get_global():
        out = "当前已注册的服务有：\n"
        count = 1
        for k in services.keys():
            out += f"{count}.{k}：{services[k]}\n" \
                      f"状态：{'已启用' if await get_status(k, 'global') else '已禁用'}\n"
            count += 1
        return out

    async def _get_special(usr: str):
        out = ""
        count = 1
        for k in services.keys():
            out += f"{count}.{k}：{'已启用' if await get_status(k, usr) else '已禁用'}\n"
            count += 1
        return out

    group = param_dict.get("g", "")
    user = param_dict.get("u", "")
    if isinstance(event, GroupMessageEvent):
        if isinstance(user, str) and user.isdigit() \
                and (await SUPERUSER(bot, event) or await GROUP_ADMIN(event) or await GROUP_OWNER(event)):
            output += f"本群用户{user}的服务状况：\n"
            output += await _get_special(f"g{str(event.group_id)}u{user}")
        elif not user:
            output += await _get_global()
            output += "本群的服务状况：\n"
            output += await _get_special(f"g{str(event.group_id)}")
    elif isinstance(group, str) and group.isdigit():
        if await SUPERUSER(bot, event):
            if not user:
                output += f"群{group}的服务状况：\n"
                output += _get_special(f"g{group}")
            elif isinstance(user, str) and user.isdigit():
                output += f"群{group}中用户{user}的服务状况：\n"
                output += _get_special(f"g{group}u{user}")
    elif param_dict.get("s"):
        if isinstance(group, str) and group.isdigit():
            output = await _get_special(f"g{group}u{event.user_id}")
        elif isinstance(event, GroupMessageEvent):
            output = await _get_special(f"g{str(event.group_id)}u{str(event.user_id)}")
        else:
            output = await _get_special(f"u{str(event.user_id)}")
    elif isinstance(user, str) and user.isdigit():
        if await SUPERUSER(bot, event):
            output += f"用户{user}的服务状况：\n"
            output += await _get_special("u" + user)
    else:
        output = await _get_global()

    out_img = Str2Img().gen_image(output)
    out = BytesIO()
    out_img.save(out, format='JPEG')

    await ls.finish(MessageSegment.image(out))


operation = on_command("enable", aliases={"disable"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@operation.handle()
async def _operation(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    enable = raw_command.endswith("enable")
    param_list, param_dict = process_command(raw_command, str(event.message))

    if not len(param_list):
        await operation.finish("缺少必要参数：服务名称")
    elif param_list[0] not in services.keys():
        await operation.finish("啊啦，该服务似乎没有注册的样子……也许这是个第三方插件？")

    service = param_list[0]
    user = param_dict.get("u")
    group = param_dict.get("g")
    if isinstance(event, GroupMessageEvent):
        usr = f"g{str(event.group_id)}"
        if isinstance(user, str) and user.isdigit():
            usr += f"u{user}"
    else:
        usr = ""
        if isinstance(group, str) and group.isdigit():
            usr += "g" + group
        if isinstance(user, str) and user.isdigit():
            usr += "u" + user
        if not usr:
            usr = "global"

    if await update_status(service, usr, enable):
        await operation.finish("操作成功！")
    else:
        await operation.finish("呜……操作失败了……")


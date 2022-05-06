from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11.utils import unescape
from nonebot.params import RawCommand
from nonebot.rule import to_me
from nonebot.typing import T_State

from src.utils.command_processor import process_command
from .sqlite import sqlite_pool
from .utils import is_group_admin, get_global_group, get_group_config

cfg = on_command("set", aliases={"setting", "设置", "群设置", "群聊设置", "群组设置"}, rule=to_me())


@cfg.handle()
async def _cfg(bot: Bot, event: MessageEvent, state: T_State, raw_command: str = RawCommand()):
    param_list, param_dict = process_command(raw_command, str(event.message))

    if not isinstance(event, GroupMessageEvent) and "group" not in param_dict.keys():
        await cfg.finish("这似乎不是一个群聊会话……请添加-group参数，在后面加上要操作的群聊的群号（数字）")
    if not param_dict.get("group", "0").isdigit():
        await cfg.finish("emmmm，提供的群号似乎不是个数字……再试一次？")

    if param_dict.get("group"):
        gid = int(param_dict["group"])
    elif isinstance(event, GroupMessageEvent):
        gid = event.group_id
    else:
        await cfg.finish()  # 感觉正常情况下不会出现……吧……前面都排除过了

    if not await is_group_admin(gid, event.user_id):
        await cfg.finish("砰！你没有管理这个群的设置的权限！")

    is_global = __str_to_bool(param_dict.get("g"))
    global_group = await get_global_group(gid)
    if is_global:
        if global_group:
            gid = global_group
        else:
            await cfg.finish("啊啦，指定的群似乎没有加入群组的说……")

    state["gid"] = gid

    if not param_list:
        await cfg.finish("emmmm，你似乎忘记提供设置的名称了……")

    match param_list[0]:
        case ("welcome" | "欢迎" | "入群" | "入群欢迎"):
            state["setting"] = "welcome"
            if len(param_list) >= 2:
                state["value"] = param_list[1]
        case ("leave" | "离开" | "退群" | "退群提醒"):
            state["setting"] = "leave"
            if len(param_list) >= 2:
                state["value"] = param_list[1]
        case ("agree" | "同意" | "自动同意" | "进群验证" | "验证消息" | "验证信息" | "验证答案"):
            state["setting"] = "autoAgreePattern"
        case ("namecard" | "群名片" | "名片格式" | "群名片格式" | "名片"):
            state["setting"] = "nameCardPattern"
        case ("namecardprompt" | "群名片提醒" | "提醒修改群名片" | "修改群名片提醒"):
            state["setting"] = "illegalNameCardPrompt"
            if len(param_list) >= 2:
                state["value"] = param_list[1]
        case _:
            await cfg.finish("砰！你似乎提供了无效的设置项……有效的项目有：欢迎、离开、验证答案、群名片格式、群名片提醒")


@cfg.got("value", "请提供设置的值")
async def _modify_cfg(bot: Bot, event: MessageEvent, state: T_State):
    value = str(state["value"])
    setting = state["setting"]
    gid = state["gid"]
    match setting:
        case ("welcome" | "leave"):
            value = value.strip()
        case ("autoAgreePattern" | "nameCardPattern"):
            value = unescape(value)
        case "illegalNameCardPrompt":
            value = __str_to_bool(value.strip())
        case _:
            raise ValueError(f"{state['setting']}不是合法的设置项，通常情况下这不应当出现，如果您未对bot进行改动，可以考虑提交一个issue")

    if isinstance(gid, str) and value == "#":
        value = None  # 控制群组设置时，不需要#，而是直接置空

    # 因为要传属性名，只能用字符串格式化了……不过不是用户直接输入的，应该不会影响安全
    await sqlite_pool.execute(f"insert into config(groupName, {setting}) values (:gid, :value) "
                              f"on conflict (groupName) do update set {setting}=:value",
                              {"value": value, "gid": gid})

    await cfg.finish(f"成功将设置项 {__setting_to_display_name(setting)} 的值更新为 {value}")


show = on_command("showset",
                  aliases={"showsetting", "showsettings", "查看设置", "查询设置", "查看群设置", "查询群设置",
                           "查看群聊设置", "查询群聊设置", "查看群组设置", "查询群组设置"}, rule=to_me())


@show.handle()
async def _show(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    msg = str(event.message).strip().removeprefix(raw_command).strip()

    if msg and msg.isdigit():
        gid = int(msg)
    elif isinstance(event, GroupMessageEvent):
        gid = event.group_id
    else:
        await show.finish("emmmm，你似乎忘记了写群号...")

    output = "本群设置有：\n"
    group_config = await get_group_config(gid, no_global=True)
    if group_config:
        output += '\n'.join([f"{__setting_to_display_name(k)}： {v}" for k, v in group_config.items()])

    global_group = await get_global_group(gid)
    if global_group:
        output += "\n本群所属的群组的设置有：\n"
        global_config = await get_group_config(global_group)
        if global_config:
            output += '\n'.join([f"{__setting_to_display_name(k)}： {v}" for k, v in global_config.items()])

    await show.finish(output)


def __str_to_bool(string: str) -> bool:
    return string in ("y", "Y", "t", "T", "true", "True", "是", True)


def __setting_to_display_name(setting: str) -> str:
    match setting:
        case "welcome":
            display_name = "入群欢迎"
        case "leave":
            display_name = "退群提醒"
        case "autoAgreePattern":
            display_name = "验证答案"
        case "nameCardPattern":
            display_name = "群名片格式"
        case "illegalNameCardPrompt":
            display_name = "修改群名片提醒"
        case _:
            display_name = "Undefined"
    return display_name

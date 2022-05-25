from nonebot import on_command, require
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.adapters.onebot.v11.utils import unescape
from nonebot.matcher import Matcher
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from src.utils.command_processor import process_command
from src.utils.str2img import Str2Img
from .config import *

# 接入服务管理器
require("service")
from ..service.rule import online

# 接入频率限制
require("ratelimit")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag

QUIT_LIST = ["取消", "算了", "退出", "0", "exit"]

new_note = on_command("添加便签", aliases={"note", "addnote", "newnote", "便签"},
                      permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
                      rule=online("notes") & gag(), state={"mode": 1}, block=True)
del_note = on_command("删除便签", aliases={"delnote", "removenote"}, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
                      rule=online("notes") & gag(), state={"mode": 2}, block=True)
mute_note = on_command("屏蔽便签", aliases={"mutenote", "disablenote"},
                       permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
                       rule=online("notes") & gag(), state={"mode": 3}, block=True)
unmute_note = on_command("解除屏蔽便签", aliases={"不屏蔽便签", "unmutenote", "enablenote"},
                         permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
                         rule=online("notes") & gag(), state={"mode": 4}, block=True)


@new_note.handle()
@del_note.handle()
@mute_note.handle()
@unmute_note.handle()
async def _new_note(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher, raw_command: str = RawCommand()):
    param_list, param_dict = process_command(raw_command, str(event.message))
    if ("g" in param_dict.keys() or "group" in param_dict.keys()) and not await SUPERUSER(bot, event):
        await matcher.finish("哒咩，权限不足！")

    if param_dict.get("g"):
        gid = 0
    else:
        gid = param_dict.get("group")
        if gid:
            if gid.isdigit():
                gid = int(gid)
            else:
                await matcher.finish("emmmm,群号似乎有误……")
        else:
            if isinstance(event, GroupMessageEvent):
                gid = event.group_id
            else:
                gid = 0

    if state["mode"] != 1:
        if not (param_list and param_list[0].isdigit()):
            await matcher.finish("emmmm……你似乎忘了提供便签id的说……")
        else:
            note_id = int(param_list[0])
            if state["mode"] == 2:
                await delete_note(gid, note_id)
            elif state["mode"] == 3:
                await mute(gid, note_id)
            else:
                await unmute(gid, note_id)
            await matcher.finish("操作成功！")
    else:
        state["gid"] = gid
        flag = 0  # 用来标记提供了几个参数
        if "t" in param_dict.keys():
            state["type"] = param_dict["t"]
            flag += 1
        if "c" in param_dict.keys():
            state["content"] = param_dict["c"]
            flag += 1
        if "r" in param_dict.keys():
            state["resp"] = param_dict["r"]
            flag += 1
        if "a" in param_dict.keys():
            state["at"] = param_dict["a"]
        elif flag == 3:
            state["at"] = False  # 如果前三个参数都提供了，但是没有"-a"，则认为不需要at


@new_note.got("type", "请提供匹配类型，有效的有：1.关键词，2.全文，3.正则，或者回复“取消”来退出")
async def _type(bot: Bot, event: MessageEvent, state: T_State):
    message = str(state["type"]).strip()
    if message in QUIT_LIST:
        await new_note.finish("OK")
    match message:
        case ("1" | "关键词" | "kwd" | "keyword"):
            state["type"] = "kwd"
        case ("2" | "全文" | "full" | "fulltext"):
            state["type"] = "full"
        case ("3" | "正则" | "re" | "reg" | "regex"):
            state["type"] = "regex"
        case _:
            await new_note.reject("匹配类型无效！请重新输入：")


@new_note.got("content", "请提供匹配使用的文字/表达式：")
async def _content(bot: Bot, event: MessageEvent, state: T_State):
    # 不检测退出是因为可能撞关键词……反正添加错了可以删（
    message = str(state["content"]).strip()
    state["content"] = unescape(message)


@new_note.got("resp", "请提供回复内容（仅支持文字）：")
async def _resp(bot: Bot, event: MessageEvent, state: T_State):
    message = str(state["resp"]).strip()
    state["resp"] = unescape(message)


@new_note.got("at", "是否要@我才能触发？y/N")
async def _at(bot: Bot, event: MessageEvent, state: T_State):
    if not isinstance(state["at"], bool):
        message = str(state["at"]).strip()
        state["at"] = message in ("Y", "y", "yes", "Yes", "YES", "是", "确定", "t", "T", "True", "true", "TRUE")

    note_id = await add_note(state["gid"], state["type"], state["content"], state["resp"], state["at"])
    await new_note.finish(f"添加成功！便签id是 {note_id}")


query_note = on_command("查询便签",
                        aliases={"listnote", "listnotes", "notelist", "noteslist", "querynote", "querynotes", "便签列表"},
                        rule=online("notes") & gag(), block=True)


@query_note.handle()
async def _query(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    param_list, param_dict = process_command(raw_command, str(event.message))
    if param_list and not await SUPERUSER(bot, event):
        await query_note.finish("哒咩，权限不足！")

    if param_dict.get("g"):
        gid = 0
    else:
        if param_list:
            gid = param_list[0]
            if gid.isdigit():
                gid = int(gid)
            else:
                await query_note.finish("emmmm,群号似乎有误……")
        else:
            if isinstance(event, GroupMessageEvent):
                gid = event.group_id
            else:
                gid = 0

    output = f"群 {gid} 的便签列表为：\n" if gid else "全局便签列表为：\n"
    notes = await get_group_notes(gid)
    for note in notes:
        output += f"ID: {note.id}\n" \
                  f"类型：{'关键词' if note.type == 'kwd' else '全文' if note.type == 'full' else '正则'}\n" \
                  f"匹配关键字：{note.content}\n" \
                  f"回复：{note.resp}\n" \
                  f"需要AT：{'是' if note.at else '否'}\n"

    if len(output) > 150:
        output = Str2Img().gen_message(output)

    await query_note.finish(output)

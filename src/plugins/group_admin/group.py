from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State

from .sqlite import sqlite_pool
from .utils import is_group_admin, get_groups_in_global_group, get_global_group

join_group = on_command("newgroup", aliases={"创建群组", "新群组", "加入群组", "joingroup", "join"}, rule=to_me(),
                        permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, state={"join": True})
leave_group = on_command("leavegroup", aliases={"离开群组", "leavegrp", "离开", "exit", "exitgroup"}, rule=to_me(),
                         permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, state={"join": False})


@join_group.handle()
@leave_group.handle()
async def _group(bot: Bot, event: GroupMessageEvent, state: T_State, raw_command: str = RawCommand()):
    join = state["join"]
    if join:
        state["name"] = str(event.message).strip().removeprefix(raw_command).strip()
        if not state["name"]:
            await join_group.finish("请在命令后提供要加入的群组名称～")
        elif state["name"][0].isdigit() or len(state["name"]) > 20:
            await join_group.finish("群组名不合法：开头不能为数字，且不能超过20位")

    current_group_name = await sqlite_pool.fetch_one("select groupName from groups where qqGroupID=:gid",
                                                     {"gid": event.group_id})
    if current_group_name:
        current_group_name = current_group_name[0]
        await bot.send(event, f"这将使本群离开当前的组{current_group_name}，确定？(y/N)")
    else:
        if not join:
            await leave_group.finish("当前没有加入任何组！")
        state["sure_leave_current"] = "True"


@join_group.got("sure_leave_current")
@leave_group.got("sure_leave_current")
async def _group_worker(bot: Bot, event: GroupMessageEvent, state: T_State):
    sure = str(state["sure_leave_current"]).strip() in ("y", "Y", "t", "T", "true", "True", "是", "确定")
    if not sure:
        if state["join"]:
            await join_group.finish("操作已中止")
        else:
            await leave_group.finish("操作已中止")

    if state["join"]:
        have_permission = False
        if await SUPERUSER(bot, event):
            have_permission = True
        else:
            groups = await get_groups_in_global_group(state["name"])
            if groups:
                for group in groups:
                    if await is_group_admin(group, event.user_id):
                        have_permission = True
                        break
            else:
                have_permission = True
        if not have_permission:
            await join_group.finish(f"抱歉，群组 {state['name']} 已存在，并且你似乎在该群组的任何一个群中都没有管理权限，因此操作被拒绝")
        else:
            await sqlite_pool.execute("insert into groups values (:gid, :gname)"
                                      "on conflict (qqGroupID) do update set groupName=:gname",
                                      {"gid": event.group_id, "gname": state["name"]})
            await join_group.finish(f"本群已成功加入群组 {state['name']}！")
    else:
        await sqlite_pool.execute("delete from groups where qqGroupID=:gid", {"gid": event.group_id})
        await leave_group.finish("本群已成功离开群组")


del_group = on_command("delgroup", aliases={"deletegroup", "删除群组"}, rule=to_me(),
                       permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@del_group.handle()
async def _del(bot: Bot, event: MessageEvent, state: T_State, raw_command: str = RawCommand()):
    msg = str(event.message).strip().removeprefix(raw_command).strip()

    if msg and not (await SUPERUSER(bot, event)):
        await del_group.finish("抱歉，你没有权限指定名称删除群组")

    if not msg:
        if isinstance(event, GroupMessageEvent):
            msg = await get_global_group(event.group_id)
        else:
            await del_group.finish("啊啦，你似乎没有提供要删除的组名的说……")

    if not await get_groups_in_global_group(msg):
        await del_group.finish("啊啦，这个组似乎不存在的说……")

    state["gname"] = msg


@del_group.got("sure", "这将使组中所所有群离开该组，并删除组的所有设置，确定吗？(y/N)")
async def _del_worker(bot: Bot, event: MessageEvent, state: T_State):
    sure = str(state["sure"]).strip() in ("y", "Y", "t", "T", "true", "True", "是", "确定")
    if not sure:
        await del_group.finish("操作已中止")

    gname = state["gname"]

    await sqlite_pool.execute("delete from config where groupName=:gname", {"gname": gname})
    await sqlite_pool.execute("delete from groups where groupName=:gname", {"gname": gname})

    await del_group.finish("操作已完成")

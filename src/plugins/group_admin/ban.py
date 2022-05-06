from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from src.utils.check_at import check_at
from src.utils.config import BotConfig
from .sqlite import sqlite_pool
from .utils import get_global_group, is_group_admin, ban_operation

# 接入帮助
default_start = list(BotConfig.command_start)[0] if BotConfig.command_start else "/"

ban = on_command("ban", aliases={"封禁", "kick", "踢"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                 state={"is_ban": True})
pardon = on_command("pardon", aliases={"解封", "unban"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                    state={"is_ban": False})

# 接入帮助
ban.__help_name__ = "ban"
ban.__help_info__ = "使用 ban/“封禁”\n" \
                    "格式为： 封禁 qq号1 qq号2\n" \
                    "或： ban @user1 @user2 \n" \
                    "当群加入群组后，这将会在整个群组内封禁该用户"
pardon.__help_name__ = "pardon"
pardon.__help_info__ = "使用 pardon/unban/解封 \n" \
                       "具体语法同封禁"


@ban.handle()
@pardon.handle()
async def _ban(bot: Bot, event: GroupMessageEvent, state: T_State, raw_command: str = RawCommand()):
    is_ban: bool = state["is_ban"]

    target = check_at(event.json())
    target += str(event.message).strip().removeprefix(raw_command).strip().split()

    target_list = [int(usr) for usr in target if (isinstance(usr, str) and usr.isdigit()) or isinstance(usr, int)]
    # check_at返回的列表里有字符串("all")和数字（用户帐号）；从消息中解出来的目标则应该是字符串形式的数字

    if target_list:
        await ban_operation(bot, event.group_id, target_list, is_ban)
        await ban.finish("操作成功！")
    else:
        await ban.finish(f"啊啦，你似乎没有提供要{'封禁' if is_ban else '解封'}的用户的说……")


ban_list = on_command("listban", aliases={"banlist", "封禁列表", "查询封禁", "已封禁用户"},
                      permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@ban_list.handle()
async def _ban_list(bot: Bot, event: GroupMessageEvent):
    global_group = await get_global_group(gid=event.group_id)
    if not global_group:
        gid = event.group_id
    else:
        gid = global_group

    ls = "被封禁的用户有：\n"
    for i in await sqlite_pool.fetch_all("select userID from ban where groupName=:gid", {"gid": gid}):
        if i:
            ls += i[0] + "\n"

    await ban_list.finish(ls)





async def check_ban(gid: int, uid: int) -> bool:
    """
    检查成员是否被ban
    :param gid: 群id
    :param uid: 用户id
    :return: bool
    """
    # 信任超管
    if str(uid) in BotConfig.superusers or uid in BotConfig.superusers:
        return False
    # 信任管理员
    if await is_group_admin(gid, uid):
        return False
    # 查询黑名单
    global_group = await get_global_group(gid)
    if global_group:
        gid = global_group

    return bool(await sqlite_pool.fetch_one("select userID from ban where groupName=:gname and userID=:uid",
                                            {"gname": gid, "uid": uid}))

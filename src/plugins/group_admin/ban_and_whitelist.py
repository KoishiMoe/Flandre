import asyncio

from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from src.utils.check_at import check_at
from src.utils.config import BotConfig
from .sqlite import sqlite_pool
from .utils import get_global_group, is_group_admin, get_groups_in_global_group

# 接入帮助
default_start = list(BotConfig.command_start)[0] if BotConfig.command_start else "/"

ban = on_command("ban", aliases={"封禁", "kick", "踢"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                 state={"operation": "ban", "status": True})
pardon = on_command("pardon", aliases={"解封", "unban"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                    state={"operation": "ban", "status": False})
whitelist = on_command("trust", aliases={"whitelist", "信任", "白名单"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                       state={"operation": "trust", "status": True})
nowhitelist = on_command("distrust", aliases={"nowhitelist", "removewhitelist", "不信任", "移出白名单", "移除白名单"},
                         permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                         state={"operation": "trust", "status": False})

# 接入帮助
ban.__help_name__ = "ban"
ban.__help_info__ = "使用 ban/“封禁”\n" \
                    "格式为： 封禁 qq号1 qq号2\n" \
                    "或： ban @user1 @user2 \n" \
                    "当群加入群组后，这将会在整个群组内封禁该用户"
pardon.__help_name__ = "pardon"
pardon.__help_info__ = "使用 pardon/unban/解封 \n" \
                       "具体语法同封禁"
whitelist.__help_name__ = "whitelist"
whitelist.__help_info__ = "使用 trust/whitelist/信任/白名单\n" \
                          "格式为： 信任 qq号1 qq号2\n" \
                          "或： trust @user1 @user2 \n" \
                          "bot将自动同意目标在本组内其他群发起的加群申请"
nowhitelist.__help_name__ = "removewhitelist"
nowhitelist.__help_info__ = "使用 distrust/nowhitelist/removewhitelist/不信任/移出白名单\n" \
                            "具体语法同信任"


@ban.handle()
@pardon.handle()
@whitelist.handle()
@nowhitelist.handle()
async def _ban(bot: Bot, event: GroupMessageEvent, state: T_State, raw_command: str = RawCommand()):
    is_ban_operation = state["operation"] == "ban"
    new_status = state["status"]

    target = check_at(event.json())
    target += str(event.message).strip().removeprefix(raw_command).strip().split()

    target_list = [int(usr) for usr in target if (isinstance(usr, str) and usr.isdigit()) or isinstance(usr, int)]
    # check_at返回的列表里有字符串("all")和数字（用户帐号）；从消息中解出来的目标则应该是字符串形式的数字

    if target_list:
        await ban_operation(bot, event.group_id, target_list, is_ban_operation, new_status)
        await ban.finish("操作成功！")
    else:
        match is_ban_operation, new_status:
            case True, True:
                tmp = "封禁"
            case True, False:
                tmp = "解封"
            case False, True:
                tmp = "加入白名单"
            case False, False:
                tmp = "移出白名单"
            case _:
                tmp = "操作"  # 真的会碰上这个吗2333
        await ban.finish(f"啊啦，你似乎没有提供要{tmp}的用户的说……")


ban_list = on_command("listban", aliases={"banlist", "封禁列表", "查询封禁", "已封禁用户", "黑名单列表"},
                      permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, state={"ban": True})
whitelist_list = on_command("whitelistlist", aliases={"trustlist", "白名单列表", "信任列表"},
                            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, state={"ban": False})


@ban_list.handle()
@whitelist_list.handle()
async def _ban_list(bot: Bot, event: GroupMessageEvent, state: T_State):
    is_ban = state["ban"]
    global_group = await get_global_group(gid=event.group_id)
    if not global_group:
        gid = event.group_id
    else:
        gid = global_group

    if is_ban:
        ls = "被封禁的用户有：\n"
        for i in await sqlite_pool.fetch_all("select userID from ban where groupName=:gid", {"gid": gid}):
            if i:
                ls += i[0] + "\n"

        await ban_list.finish(ls)
    else:
        ls = "白名单有：\n"
        for i in await sqlite_pool.fetch_all(
                "select userID from whitelist where groupName=:gname",
                {"gname": gid}):
            if i:
                ls += i[0] + "\n"
        await whitelist_list.finish(ls)


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


async def check_trust(gid: int, uid: int) -> bool:
    # 信任超管
    if str(uid) in BotConfig.superusers or uid in BotConfig.superusers:
        return True
    # 信任管理员
    if await is_group_admin(gid, uid):
        return True
    global_group = await get_global_group(gid)
    if global_group:
        gid = global_group
    # 白名单用户
    return bool(await sqlite_pool.fetch_one("select userID from whitelist where groupName=:gname and userID=:uid",
                                            {"gname": gid, "uid": uid}))


async def ban_operation(bot: Bot, gid: int, target_list: list[int], is_ban_operation: bool, new_status: bool):
    global_group = await get_global_group(gid)

    if is_ban_operation:
        if new_status:
            if global_group:
                groups = await get_groups_in_global_group(global_group)
            else:
                groups = {gid}
            for target in target_list:
                for group in groups:
                    try:
                        await bot.set_group_kick(group_id=group, user_id=target, reject_add_request=False)
                        # 设成True的话bot就没法解封了
                        await asyncio.sleep(1)
                    except Exception as e:
                        logger.info(f"从群{group}中踢出用户{target}时发生了错误：{e}")  # 因为用户可能不在群里，所以要把异常捕捉一下……

            await sqlite_pool.execute_many("insert into ban values (:gname, :uid) "
                                           "on conflict (groupName, userID) do nothing ",
                                           [{
                                               "gname": global_group or gid,
                                               "uid": target
                                           } for target in target_list])
            await ban_operation(bot, gid, target_list, False, False)  # 移除白名单
        else:
            await sqlite_pool.execute_many("delete from ban where groupName=:gname and userID=:uid",
                                           [{"gname": global_group or gid,
                                             "uid": target} for target in target_list])
    else:
        if new_status:
            await sqlite_pool.execute_many("insert into whitelist values (:gname, :user) "
                                           "on conflict (groupName, userID) do nothing ",
                                           [{"gname": global_group or gid, "user": target} for target in target_list])
            await ban_operation(bot, gid, target_list, True, False)  # 移除黑名单
        else:
            await sqlite_pool.execute_many("delete from whitelist where groupName=:gname and userID=:user",
                                           [{"gname": global_group or gid, "user": target} for target in target_list])

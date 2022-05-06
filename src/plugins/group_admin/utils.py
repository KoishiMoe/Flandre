import asyncio

from nonebot import get_bot, logger
from nonebot.adapters.onebot.v11 import Bot

from src.utils.config import BotConfig
from .sqlite import sqlite_pool


async def get_global_group(gid: int) -> str | None:
    global_group = await sqlite_pool.fetch_one("select groupName from groups where qqGroupID=:gid", {"gid": gid})
    if global_group:
        return global_group[0]


async def get_group_config(group_name: int | str, no_global: bool = False) -> dict:
    """
    获取指定群的设置
    :param group_name: 群号或群组名
    :param no_global: 本群未配置时是否使用群组的配置代替
    :return: dict
    """
    def __getcfg(order: int):
        local = local_config.get(order)
        if local is None and not no_global:
            return global_config.get(order)
        return local

    local_config = await sqlite_pool.fetch_one("select * from config where groupName=:gname",
                                               {"gname": str(group_name)})
    if not local_config:
        local_config = {}
    else:
        local_config = dict(enumerate(local_config))

    if not no_global:
        global_config = {}

        global_group = await get_global_group(group_name) if isinstance(group_name, int) else None
        if global_group:
            global_config = await sqlite_pool.fetch_one("select * from config where groupName=:gname",
                                                        {"gname": global_group})
            global_config = dict(enumerate(global_config))

    config = {
        "welcome": __getcfg(1),
        "leave": __getcfg(2),
        "autoAgreePattern": __getcfg(3),
        "nameCardPattern": __getcfg(4),
        "illegalNameCardPrompt": __getcfg(5),
    }

    return config


async def is_group_admin(gid: int, uid: int) -> bool:
    if uid in BotConfig.superusers or str(uid) in BotConfig.superusers:
        return True
    bot: Bot = get_bot()
    try:
        member_info = await bot.get_group_member_info(group_id=gid, user_id=uid, no_cache=True)
        return member_info.get("role") in ("owner", "admin")
    except Exception as e:
        logger.warning(f"获取群{gid}成员{uid}的信息时发生了错误：{e}")
        return False


async def get_groups_in_global_group(gname: str) -> set[int]:
    groups = await sqlite_pool.fetch_all(
        "select qqGroupID from groups where groupName=:gname",
        {"gname": gname})
    groups = set([int(i[0]) for i in groups if i])

    return groups


# 这俩为啥扔在这？
# 答案是不扔在这会循环导入（（（

async def ban_operation(bot: Bot, gid: int, target_list: list[int], is_ban: bool):
    global_group = await get_global_group(gid)
    if global_group:
        groups = await get_groups_in_global_group(global_group)
    else:
        groups = {gid}

    if is_ban:
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
        await whitelist_operation(bot, gid, target_list, False)  # 移除白名单
    else:
        await sqlite_pool.execute_many("delete from ban where groupName=:gname and userID=:uid",
                                       [{"gname": global_group or gid,
                                         "uid": target} for target in target_list])


async def whitelist_operation(bot: Bot, gid: int, target_list: list[int], is_trust: bool):
    global_group = await get_global_group(gid)

    if is_trust:
        await sqlite_pool.execute_many("insert into whitelist values (:gname, :user) "
                                       "on conflict (groupName, userID) do nothing ",
                                       [{"gname": global_group or gid, "user": target} for target in target_list])
        await ban_operation(bot, gid, target_list, False)
    else:
        await sqlite_pool.execute_many("delete from whitelist where groupName=:gname and userID=:user",
                                       [{"gname": global_group or gid, "user": target} for target in target_list])

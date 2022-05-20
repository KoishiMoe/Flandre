from nonebot.log import logger

from .sqlite import sqlite_pool


async def get_status(service: str, user: str) -> bool:
    enabled = await sqlite_pool.fetch_one("select state from service where service=:service and user=:user",
                                          {"service": service, "user": user})
    if enabled is None:
        await update_status(service, user, True)
        enabled = [True]

    return enabled[0]


async def update_status(service: str, user: str, state: bool = True) -> bool:
    try:
        await sqlite_pool.execute("insert into service values (:service, :user, :state) "
                                  "on conflict (service, user) do update set state=:state",
                                  {"service": service, "user": user, "state": state})
        return True
    except Exception as e:
        logger.warning(f"更新服务`{service}`对用户`{user}`的状态至`{state}`时发生了异常：{e}")
        return False

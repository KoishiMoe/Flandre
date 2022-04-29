import os
from pathlib import Path

from nonebot import get_driver, logger
from databases import Database

driver = get_driver()

os.makedirs("data/database/utils", exist_ok=True)
__db_exists = (Path(".") / "data" / "database" / "utils" / "utils.sqlite").is_file()
sqlite_pool = Database("sqlite:///data/database/utils/utils.sqlite")


@driver.on_startup
async def sqlite_connect():
    await sqlite_pool.connect()
    logger.info("成功连接到系统工具数据库")
    if not __db_exists:
        await sqlite_pool.execute(
            """
            create table if not exists exceptions(
                track_id varchar(11) primary key ,
                exc_time char(19) null,
                exc_type varchar(50) null,
                exc_value text null ,
                trace text null 
            );
            """
        )
        logger.info("成功初始化系统工具数据库")


@driver.on_shutdown
async def sqlite_disconnect():
    await sqlite_pool.disconnect()
    logger.info("成功断开与系统工具数据库的连接")

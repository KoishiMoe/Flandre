import os
from pathlib import Path

from nonebot import get_driver, logger
from databases import Database

driver = get_driver()

os.makedirs("data/database/notes", exist_ok=True)
__db_exists = (Path(".") / "data" / "database" / "notes" / "notes.sqlite").is_file()
sqlite_pool = Database("sqlite:///data/database/notes/notes.sqlite")

ddl = """
    create table if not exists notes(
        gid int not null ,
        noteID int not null ,
        type varchar(10) not null ,
        matcherContent ntext not null ,
        resp ntext not null ,
        at bool false,
        primary key (gid, noteID)
    );
    create table if not exists mute(
        gid int not null ,
        noteID int not null ,
        primary key (gid, noteID)
    );
"""


@driver.on_startup
async def sqlite_connect():
    await sqlite_pool.connect()
    logger.info("成功连接到便签数据库")
    if not __db_exists:
        for query in ddl.split(";"):
            await sqlite_pool.execute(query)
        logger.info("成功初始化便签数据库")


@driver.on_shutdown
async def sqlite_disconnect():
    await sqlite_pool.disconnect()
    logger.info("成功断开与便签数据库的连接")

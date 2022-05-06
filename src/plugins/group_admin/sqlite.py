import os
from pathlib import Path

from nonebot import get_driver, logger
from databases import Database

driver = get_driver()

os.makedirs("data/database/group_admin", exist_ok=True)
__db_exists = (Path(".") / "data" / "database" / "group_admin" / "group_admin.sqlite").is_file()
sqlite_pool = Database("sqlite:///data/database/group_admin/group_admin.sqlite")

ddl = """
    create table if not exists groups(
        qqGroupID varchar(15) primary key ,
        groupName nvarchar(20) null 
    );
    create table if not exists ban(
        groupName nvarchar(20) not null ,
        userID varchar(15) not null ,
        primary key (groupName, userID)
    );
    create table if not exists whitelist(
        groupName nvarchar(20) not null ,
        userID varchar(15) not null ,
        primary key (groupName, userID)
    );
    create table if not exists config(
        groupName nvarchar(20) primary key ,
        welcome text null ,
        leave text null ,
        autoAgreePattern text null ,
        nameCardPattern text null ,
        illegalNameCardPrompt boolean null 
    );
"""


@driver.on_startup
async def sqlite_connect():
    await sqlite_pool.connect()
    logger.info("成功连接到群管数据库")
    if not __db_exists:
        for query in ddl.split(";"):
            await sqlite_pool.execute(query)
        logger.info("成功初始化群管数据库")


@driver.on_shutdown
async def sqlite_disconnect():
    await sqlite_pool.disconnect()
    logger.info("成功断开与群管数据库的连接")

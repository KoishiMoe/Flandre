#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot
from nonebot.adapters.onebot.v11 import Adapter
from nonebot.log import logger, default_format

from src.utils.config import RUNTIME_CONFIG
from src.utils.third_party_plugin import init_3rd_plugin

# Custom your logger

# error强制记录，warning和info视log_level以及调试模式是否打开，debug仅在调试模式下启用
if RUNTIME_CONFIG["debug"]:
    logger.add("data/logs/debug/debug.log",
               rotation="00:00",
               diagnose=False,
               level="DEBUG",
               format=default_format)
elif RUNTIME_CONFIG["log_level"] >= 2:
    logger.add("data/logs/info/info.log",
               rotation="00:00",
               diagnose=False,
               level="INFO",
               format=default_format)
elif RUNTIME_CONFIG["log_level"] == 1:
    logger.add("data/logs/warning/warning.log",
               rotation="00:00",
               diagnose=False,
               level="WARNING",
               format=default_format)
else:
    logger.add("data/logs/error/error.log",
               rotation="00:00",
               diagnose=False,
               level="ERROR",
               format=default_format)

# You can pass some keyword args config to init function
nonebot.init(**RUNTIME_CONFIG)
app = nonebot.get_asgi()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)

# 测试用
if RUNTIME_CONFIG["debug"]:
    nonebot.load_builtin_plugins()

# Please DO NOT modify this file unless you know what you are doing!
# As an alternative, you should use command `nb` or modify `pyproject.toml` to load plugins
nonebot.load_from_toml("pyproject.toml")

# 加载用户定义的第三方插件
if init_3rd_plugin():
    nonebot.load_from_json("plugins.json")
else:
    logger.info("未找到有效的第三方插件配置，已跳过加载")

# Modify some config / config depends on loaded configs

config = driver.config
# do something...


if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from importlib.util import find_spec

import nonebot
from nonebot.adapters.cqhttp import Bot as Flandre

from src.utils.config import RUNTIME_CONFIG

# Custom your logger
# 
from nonebot.log import logger, default_format
# error强制记录，warning和info视log_level以及调试模式是否打开，debug仅在调试模式下启用
logger.add("data/logs/error/error.log",
           rotation="00:00",
           diagnose=False,
           level="ERROR",
           format=default_format)
if RUNTIME_CONFIG["log_level"] >= 1 or RUNTIME_CONFIG["debug"]:
    logger.add("data/logs/warning/warning.log",
               rotation="00:00",
               diagnose=False,
               level="WARNING",
               format=default_format)
if RUNTIME_CONFIG["log_level"] >= 2 or RUNTIME_CONFIG["debug"]:
    logger.add("data/logs/info/info.log",
               rotation="00:00",
               diagnose=False,
               level="INFO",
               format=default_format)
if RUNTIME_CONFIG["debug"]:
    logger.add("data/logs/debug/debug.log",
               rotation="00:00",
               diagnose=False,
               level="DEBUG",
               format=default_format)

# You can pass some keyword args config to init function
nonebot.init(**RUNTIME_CONFIG)
app = nonebot.get_asgi()

driver = nonebot.get_driver()
driver.register_adapter("cqhttp", Flandre)

# 测试用
if RUNTIME_CONFIG["debug"]:
    nonebot.load_builtin_plugins()

# 帮助系统
if RUNTIME_CONFIG["use_local_help"]:
    nonebot.load_plugin("nonebot_plugin_help")

# Please DO NOT modify this file unless you know what you are doing!
# As an alternative, you should use command `nb` or modify `pyproject.toml` to load plugins
nonebot.load_from_toml("pyproject.toml")

# Modify some config / config depends on loaded configs
# 
config = driver.config
# do something...


if __name__ == "__main__":
    # nonebot.logger.warning("Always use `nb run` to start the bot instead of manually running!")
    nonebot.run(app="__mp_main__:app")

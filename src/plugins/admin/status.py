from datetime import datetime
from os import popen
from time import time

import psutil
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.plugin import require

from src.utils.config import BotConfig
from src.utils.str2img import Str2Img

# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

register("status", "运行状况检查")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag

# 接入帮助
default_start = list(BotConfig.command_start)[0] if BotConfig.command_start else "/"

status = on_command("status", rule=online("status") & gag())

# 接入帮助
status.__help_name__ = "status"
status.__help_info__ = "status  获取简易运行状态\n" \
                       "下面的因为可能涉及敏感信息，仅能由超管使用，推荐私聊查询\n" \
                       "status d  获取详细系统信息\n" \
                       "status n  获取neofetch输出（需要系统中安装了neofetch）\n" \
                       "status s  获取screenfetch输出（需要系统中安装了screenfetch）"


@status.handle()
async def _status(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    param = str(event.message).strip().removeprefix(raw_command).strip()
    detail = await SUPERUSER(bot, event) and param in ("d", "-d", "detail", "full")
    neofetch = await SUPERUSER(bot, event) and param in ("n", "-n", "neofetch")
    screenfetch = await SUPERUSER(bot, event) and param in ("s", "-s", "screenfetch")

    if detail:
        await status.finish(await __get_full())
    elif neofetch:
        await status.finish(await __fetch(neo=True))
    elif screenfetch:
        await status.finish(await __fetch(neo=False))
    else:
        await status.finish(await __get_lite())


async def __get_lite():
    output = ""

    cpu = psutil.cpu_percent(1)
    output += f"CPU：{cpu}%"

    mem = psutil.virtual_memory()
    # 如果直接用mem.total，可能因为前后时间内内存占用的变化导致百分比与mem.used/mem.total出现偏差
    used = mem.used / 1024 / 1024
    total = mem.total / 1024 / 1024
    output += f"\n内存：{used:.2f}MiB/{total:.2f}MiB （{used / total * 100:.2f}%）"

    disk = psutil.disk_usage("/")
    output += f"\n磁盘：{disk.used / 1024 / 1024 / 1024:.2f}GiB/{disk.total / 1024 / 1024 / 1024:.2f}GiB ({disk.percent}%)"

    net = psutil.net_io_counters()
    output += f"\n网络：{net.bytes_sent / 1024 / 1024:.2f}MiB sent/{net.bytes_recv / 1024 / 1024:.2f}MiB recv"

    boot_time = psutil.boot_time()
    up_time = str(
        datetime.utcfromtimestamp(time()).replace(microsecond=0)
        - datetime.utcfromtimestamp(boot_time).replace(microsecond=0)
    )
    output += f"\n运行时间：{up_time}"

    if cpu > 90 or mem.percent > 90 or disk.percent > 90:
        output = "我好像有点累了o(╥﹏╥)o\n" + output
    else:
        output = "报告主人，一切正常ヾ(≧∇≦*)ゝ\n" + output

    return output


async def __get_full():
    output = ""

    # CPU
    cpu_times = "\n       ".join(str(psutil.cpu_times()).removeprefix("scputimes(").removesuffix(")").split(","))
    cpu_times_percent = "\n       ".join(str(psutil.cpu_times_percent(interval=1))
                                         .removeprefix("scputimes(").removesuffix(")").split(","))
    stats = "\n       ".join(str(psutil.cpu_stats()).removeprefix("scpustats(").removesuffix(")").split(","))
    output += f"""CPU:
    count: {psutil.cpu_count()} logical, {psutil.cpu_count(logical=False)} physical
    percent: {psutil.cpu_percent(interval=1, percpu=True)} ({psutil.cpu_percent(interval=1)} total)
    cpu_times: 
        {cpu_times}
    cpu_times_percent: 
        {cpu_times_percent}
    stats: 
        {stats}
"""
    # Mem
    vm_list = "\n       ".join(str(psutil.virtual_memory()).removeprefix("svmem(").removesuffix(")").split(","))
    sw_list = "\n       ".join(str(psutil.swap_memory()).removeprefix("sswap(").removesuffix(")").split(","))
    output += f"""Memory:
    virtual_memory: 
        {vm_list}
    swap_memory: 
        {sw_list}
"""
    # Disk
    parts = psutil.disk_partitions()
    # 单行显示的话长度感人，不切开的话会炸
    paths = [part.mountpoint for part in parts]
    usages = "\n        ".join([f"{path}: {psutil.disk_usage(path)}".removeprefix("sdiskusage(").removesuffix(")")
                                for path in paths])
    io_counters = '\n        '.join(
        str(psutil.disk_io_counters()).removeprefix("sdiskio(").removesuffix(")").split(","))
    output += f"""Disk:
    usage: 
        {usages}
    io_counters: 
        {io_counters}
"""
    # Network
    net_io_counter = '\n       '.join(str(psutil.net_io_counters())
                                      .removeprefix("snetio(").removesuffix(")").split(","))
    if_addrs = ""
    for k, v in psutil.net_if_addrs().items():
        if_addrs += f"\n        {k}: "
        for addr in v:
            if_addrs += f"\n            ip: {addr.address}  netmask: {addr.netmask}"
    if_stats = ""
    for k, v in psutil.net_if_stats().items():
        if_stats += f"\n        {k}: {str(v).removeprefix('snicstats(').removesuffix(')')}"
    output += f"""Network:
    io_counter: 
        {net_io_counter}
    if_addrs: {if_addrs}
    if_stats: {if_stats}
"""
    # Misc
    user_list = ""
    for user in psutil.users():
        user_list += f"\n        name: {user.name}" \
                     f"\n        terminal: {user.terminal}" \
                     f"\n        host: {user.host}" \
                     f"\n        started: {datetime.utcfromtimestamp(user.started).replace(microsecond=0)} UTC" \
                     f"\n        pid: {user.pid}"
    output += f"""Misc:
    users: {user_list}
    boot_time: {datetime.utcfromtimestamp(psutil.boot_time())} UTC
"""

    return Str2Img(width=0).gen_message(output)


async def __fetch(neo: bool = True):
    fetch = popen(r"neofetch --stdout" if neo else r"screenfetch -nN")
    out_str = '\n'.join(fetch.readlines())

    output = Str2Img(width=0).gen_message(out_str)

    return output

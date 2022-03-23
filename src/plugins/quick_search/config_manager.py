import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from src.utils.config import RUNTIME_CONFIG
from .config import Config

QUIT_LIST = ["取消", "quit", "退出"]

add_engine = on_command("search.add", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@add_engine.handle()
async def _add_engine(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.message).strip().removeprefix("search.add")
    state["global"] = msg == '.global'

    if state["global"] and event.user_id not in RUNTIME_CONFIG["superusers"]:
        return


@add_engine.got("prefix", "请回复前缀，或回复“取消”以退出")
async def _add_engine_prefix(bot: Bot, event: MessageEvent, state: T_State):
    prefix = str(state['prefix']).strip()
    state['prefix'] = prefix

    if prefix in QUIT_LIST:
        await add_engine.finish("OK")
    elif re.findall(r'\W', prefix):
        await add_engine.reject("前缀含有非法字符，请重新输入！")


@add_engine.got("url", "请回复搜索引擎网址，形如 https://www.example.com/search?q=%s")
async def _add_engine_url(bot: Bot, event: MessageEvent, state: T_State):
    url = str(state['url']).strip()
    state['url'] = url

    if url in QUIT_LIST:
        await add_engine.finish("OK")
    elif not re.match(r'^https?:/{2}\w.+$', url):
        await add_engine.reject("非法url!请重新输入！")

    gid = event.group_id if isinstance(event, GroupMessageEvent) else 0
    cfg: Config = Config(gid)

    if cfg.add_engine(state['prefix'], url, glob=state['global']):
        await add_engine.finish(f"添加搜索引擎{state['prefix']}成功！")
    else:
        await add_engine.finish("呜……失败了……")


list_engine = on_command("search.list")


@list_engine.handle()
async def _list_engine(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.message).strip().removeprefix("search.list")
    glob = msg == '.global'

    if not glob:
        if isinstance(event, GroupMessageEvent):
            cfg = Config(event.group_id)
            engine_list = cfg.list_data(glob=False)
            engine_list = engine_list if engine_list else "呜，本群似乎还没有设置搜索引擎的说……"
            await list_engine.finish(engine_list)
    else:
        cfg = Config(0)
        engine_list = cfg.list_data(glob=True)
        engine_list = engine_list if engine_list else "呜……管理员似乎还没有设置全局搜索引擎的说"
        await list_engine.finish(engine_list)

    return


delete_engine = on_command("search.delete", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@delete_engine.handle()
async def _delete_engine(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.message).strip().removeprefix("search.delete")
    state["global"] = msg == '.global'

    if state["global"] and event.user_id not in RUNTIME_CONFIG["superusers"]:
        return


@delete_engine.got("prefix", "请回复前缀，或回复“取消”以退出")
async def _delete_engine_prefix(bot: Bot, event: MessageEvent, state: T_State):
    prefix = str(state['prefix']).strip()
    state['prefix'] = prefix

    if prefix in QUIT_LIST:
        await delete_engine.finish("OK")
    elif re.findall(r'\W', prefix):
        await delete_engine.reject("前缀含有非法字符，请重新输入！")

    gid = event.group_id if isinstance(event, GroupMessageEvent) else 0
    cfg = Config(gid)

    if cfg.del_engine(state['prefix'], glob=state['global']):
        await delete_engine.finish(f"删除搜索引擎{state['prefix']}成功！")
    else:
        await delete_engine.finish("呜……失败了……")

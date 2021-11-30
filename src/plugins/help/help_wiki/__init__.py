from nonebot import on_command
from nonebot.adapters.cqhttp import Bot, MessageEvent
from nonebot.rule import to_me
from nonebot.typing import T_State

from .data_source import Helper

'''
TODO:有接入nonebot-plugin-help的计划，用户无需担心后续过度依赖wiki站的问题
'''

main_help = on_command("帮助", aliases={"菜单", "帮助信息", "help", "menu"}, rule=to_me())


@main_help.handle()
async def _main_help(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.message).strip()
    if len(msg) == 0:
        repo = await Helper.main_menu()
    else:
        repo = await Helper.get_title(msg)
    await main_help.finish(repo)


about_me = on_command("关于", aliases={"about"}, rule=to_me())


@about_me.handle()
async def _about_me(bot: Bot, event: MessageEvent):
    repo = await Helper.about_me()
    await about_me.finish(repo)


service_list = on_command("列表", aliases={"服务列表", "功能列表"}, rule=to_me())


@service_list.handle()
async def _service_list(bot: Bot, event: MessageEvent):
    repo = await Helper.service_list()
    await service_list.finish(repo)

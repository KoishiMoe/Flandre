from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.rule import to_me

from .data_source import Helper


main_help = on_command("帮助", aliases={"help"}, rule=to_me())


@main_help.handle()
async def _main_help(event: MessageEvent):
    msg = str(event.message).strip().removeprefix("帮助").removeprefix("help").lstrip()
    if len(msg) == 0:
        repo = await Helper.main_menu()
    else:
        repo = await Helper.get_title(msg)
    await main_help.finish(repo)


about_me = on_command("关于", aliases={"about"}, rule=to_me())


@about_me.handle()
async def _about_me():
    repo = await Helper.about_me()
    await about_me.finish(repo)


service_list = on_command("列表", aliases={"服务列表", "功能列表"}, rule=to_me())


@service_list.handle()
async def _service_list():
    repo = await Helper.service_list()
    await service_list.finish(repo)

import nonebot.plugin
from nonebot import on_command
from nonebot.adapters import Event
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Arg

from src.utils.str2img import Str2Img

# 接入服务管理器
nonebot.plugin.require("service")
from ..service.rule import online

# 接入禁言检查
nonebot.plugin.require("utils")
from ..utils.gag import not_gagged as gag

# 接入频率限制
nonebot.plugin.require("ratelimit")
from ..ratelimit.config_manager import register as register_ratelimit
from ..ratelimit.rule import limit

register_ratelimit("help", "帮助")

default_start = list(nonebot.get_driver().config.command_start)[0]
helper = on_command("help", priority=1, aliases={"帮助"}, rule=online("help") & gag() & limit("help"))
helper.__help_name__ = 'help'
helper.__help_info__ = f'''{default_start}help  # 获取本插件帮助
{default_start}help list  # 展示已加载插件列表
{default_start}help <plugin_name>  # 调取目标插件帮助信息'''


@helper.handle()
async def handle_first_receive(event: Event, matcher: Matcher, args: Message = CommandArg()):
    at = MessageSegment.at(event.get_user_id())
    if args:
        matcher.set_arg("content", args)
    else:
        await matcher.finish(Message(at + f'''欢迎使用Nonebot 2 Help Plugin
支持使用的前缀：{" ".join(list(nonebot.get_driver().config.command_start))}
{default_start}help  # 获取本插件帮助
{default_start}help list  # 展示已加载插件列表
{default_start}help <plugin_name>  # 调取目标插件帮助信息
'''))


@helper.got("content")
async def get_result(event: Event, content: Message = Arg()):
    args = content.extract_plain_text().split()
    if str(args[0]).lower() == "list":
        plugin_set = nonebot.plugin.get_loaded_plugins()
        plugin_names = []
        for plugin in plugin_set:
            try:
                name = f'{plugin.name} | ' \
                       f'{plugin.module.__getattribute__("__help_plugin_name__")}'
            except AttributeError:
                name = f'{plugin.name}'
            try:
                version = plugin.module.__getattribute__("__help_version__")
            except AttributeError:
                version = ""
            plugin_names.append(f'{name} {version}')
        plugin_names.sort()
        newline_char = '\n'
        result = f'已加载插件：\n{newline_char.join(plugin_names)}'
    else:
        try:
            plugin = nonebot.plugin.get_plugin(args[0])
        except AttributeError:
            plugin = None
        try:
            matchers = plugin.matcher
            infos = {}
            index = 1
            for matcher in matchers:
                try:
                    name = matcher.__help_name__
                except AttributeError:
                    name = None
                try:
                    help_info = matcher.__help_info__
                except AttributeError:
                    help_info = matcher.__doc__
                if name and help_info:
                    infos[f'{index}. {name}'] = help_info
                    index += 1
            results = [plugin.module.__getattribute__("__usage__")]
            if infos:
                results.extend(("", "序号. 命令名: 命令用途"))
                results.extend(
                    [f'{key}: {value}' for key, value in infos.items()
                     if key and value]
                )
            result = '\n'.join(results)
        except Exception:
            try:
                result = plugin.module.__doc__
            except AttributeError:
                result = f'{args[0]}插件不存在或未加载'

    if len(result) > 100:
        result = Str2Img().gen_message(result)
    if isinstance(event, GroupMessageEvent):
        result = MessageSegment.at(event.user_id) + result
    await helper.finish(result)

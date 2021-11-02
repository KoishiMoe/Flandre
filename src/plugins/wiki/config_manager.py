import re
from typing import Type

from mediawiki import MediaWiki
from nonebot import on_command
from nonebot.adapters.cqhttp import Bot, GroupMessageEvent, Event, Message
from nonebot.adapters.cqhttp.permission import GROUP_OWNER, GROUP_ADMIN, GROUP, PRIVATE
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from .config import Config


def _gen_prompt_template(prompt: str):
    if hasattr(Message, 'template'):
        return Message.template(prompt)
    return prompt


def do_add_wiki(add_wiki: Type[Matcher]):
    @add_wiki.handle()
    async def init_promote(bot: Bot, event: Event, state: T_State):
        state['_prompt'] = "请输入要添加的Wiki的代号（只允许使用字母、数字、下划线），这将作为条目名前用于标识的前缀，因此请尽可能简短且易于记忆\n" + \
                           "例如，如果将“萌娘百科”的代号设置为moe，则从中搜索条目“芙兰朵露“的语法即为：\n" + \
                           "[[moe:芙兰朵露]]\n" + \
                           "另请注意：mediawiki常用的名字空间及其缩写将不会被允许作为代号，例如Special、Help、Template、Draft等。" + \
                           "也不建议将要绑定的wiki的项目名字空间作为代号，否则可能产生冲突\n" + \
                           "回复“取消”以中止"

    async def parse_prefix(bot: Bot, event: Event, state: T_State) -> None:
        prefix = str(event.get_message()).strip().lower()
        reserved = ["(main)", "talk", "user", "user talk", "project", "project talk", "file", "file talk", "mediawiki",
                    "mediawiki talk", "template", "template talk", "help", "help talk", "category", "category talk",
                    "special", "media", "t", "u"]
        if prefix == "取消":
            await add_wiki.finish("OK")
        elif prefix in reserved:
            await add_wiki.reject("前缀位于保留名字空间！请重新输入！")
        elif re.findall('\W', prefix):
            await add_wiki.reject("前缀含有非法字符！请重新输入！")
        else:
            state['prefix'] = prefix

    @add_wiki.got('prefix', _gen_prompt_template('{_prompt}'), parse_prefix)
    @add_wiki.handle()
    async def init_api_url(bot: Bot, event: Event, state: T_State):
        state['_prompt'] = "请输入wiki的api地址，通常形如这样：\n" + \
                           "https://www.example.org/w/api.php\n" + \
                           "https://www.example.org/api.php\n" \
                           "如果托管bot的服务器所在的国家/地区无法访问某些wiki的api，或者该wiki不提供api,你也可以回复empty来跳过输入"

    async def parse_api_url(bot: Bot, event: Event, state: T_State):
        api_url = str(event.get_message()).strip()
        if api_url.lower() == 'empty':
            state['api_url'] = ''
        elif api_url == '取消':
            await add_wiki.finish("OK")
        elif not re.match(r'^https?:/{2}\w.+$', api_url):
            await add_wiki.reject("非法url!请重新输入！")
        else:
            try:
                test_wiki = MediaWiki(url=api_url)
            except:
                await add_wiki.reject("无法连接到api，请重新输入！如果确认无误的话，可能是被防火墙拦截，可以输入“empty”跳过，或者“取消”来退出")
            state['api_url'] = api_url.strip().rstrip("/")

    @add_wiki.got('api_url', _gen_prompt_template('{_prompt}'), parse_api_url)
    @add_wiki.handle()
    async def init_url(bot: Bot, event: Event, state: T_State):
        state['_prompt'] = '请输入wiki的通用url，通常情况下，由该url与条目名拼接即可得到指向条目的链接，如：\n' + \
                           '中文维基百科：https://zh.wikipedia.org/wiki/\n' + \
                           '萌娘百科：https://zh.moegirl.org.cn/\n' + \
                           '另请注意：该项目不允许置空'

    async def parse_url(bot: Bot, event: Event, state: T_State):
        url = str(event.get_message()).strip()
        if url == "取消":
            await add_wiki.finish("OK")
        elif not re.match(r'^https?:/{2}\w.+$', url):
            await add_wiki.reject("非法url！请重新输入！")
        else:
            state['url'] = url.strip().rstrip("/")

    @add_wiki.got('url', _gen_prompt_template('{_prompt}'), parse_url)
    @add_wiki.handle()
    async def add_wiki_process(bot: Bot, event: GroupMessageEvent, state: T_State):
        config: Config = Config(event.group_id)
        prefix: str = state["prefix"]
        api_url: str = state["api_url"]
        url: str = state["url"]
        if config.add_wiki(prefix, api_url, url):
            await add_wiki.finish(f"添加Wiki: {prefix} 成功！")
        else:
            await add_wiki.finish("呜……出错了……如果持续出现，请联系bot管理员进行排查")


def do_query_wikis(query_wikis: Type[Matcher]):
    @query_wikis.handle()
    async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
        config: Config = Config(event.group_id)
        all_data: tuple = config.list_data
        all_data_str: str = all_data[0] + "--------------------\n" + all_data[1]
        await query_wikis.finish(all_data_str)


def do_del_wiki(del_wiki: Type[Matcher]):
    @del_wiki.handle()
    async def send_list(bot: Bot, event: GroupMessageEvent, state: T_State):
        config: Config = Config(event.group_id)
        res = "以下为本群绑定的所有wiki列表，请回复前缀来选择要删除的wiki，回复“取消”退出：\n"
        res += config.list_data[0]
        await del_wiki.send(message=Message(res))

    @del_wiki.receive()
    async def do_del(bot, event: GroupMessageEvent, state: T_State):
        prefix = str(event.get_message()).strip()
        if prefix == "取消":
            await del_wiki.finish("OK")
        else:
            config: Config = Config(event.group_id)
            if config.del_wiki(prefix):
                await del_wiki.finish("删除成功")
            else:
                await del_wiki.finish("删除失败……请检查前缀是否有误")


def do_set_default(set_default: Type[Matcher]):
    @set_default.handle()
    async def send_list(bot: Bot, event: GroupMessageEvent, state: T_State):
        config: Config = Config(event.group_id)
        res = "以下为本群绑定的所有wiki列表，请回复前缀来选择要设为默认的wiki，回复“取消”退出：\n"
        res += config.list_data[0]
        await set_default.send(message=Message(res))

    @set_default.receive()
    async def do_set(bot, event: GroupMessageEvent, state: T_State):
        prefix = str(event.get_message()).strip()
        if prefix == "取消":
            await set_default.finish("OK")
        else:
            config: Config = Config(event.group_id)
            if config.set_default(prefix):
                await set_default.finish("设置成功")
            else:
                await set_default.finish("设置失败……请检查前缀是否有误")


'''
全局wiki设置
'''


def do_add_wiki_global(add_wiki_global: Type[Matcher]):
    @add_wiki_global.handle()
    async def init_promote(bot: Bot, event: Event, state: T_State):
        state['_prompt'] = "请输入要添加的Wiki的代号（只允许使用字母、数字、下划线），这将作为条目名前用于标识的前缀，因此请尽可能简短且易于记忆\n" + \
                           "例如，如果将“萌娘百科”的代号设置为moe，则从中搜索条目“芙兰朵露“的语法即为：\n" + \
                           "[[moe:芙兰朵露]]\n" + \
                           "另请注意：mediawiki常用的名字空间及其缩写将不会被允许作为代号，例如Special、Help、Template、Draft等。" + \
                           "也不建议将要绑定的wiki的项目名字空间作为代号，否则可能产生冲突\n" + \
                           "回复“取消”以中止"

    async def parse_prefix(bot: Bot, event: Event, state: T_State) -> None:
        prefix = str(event.get_message()).strip().lower()
        reserved = ["(main)", "talk", "user", "user talk", "project", "project talk", "file", "file talk", "mediawiki",
                    "mediawiki talk", "template", "template talk", "help", "help talk", "category", "category talk",
                    "special", "media", "t", "u"]
        if prefix == "取消":
            await add_wiki_global.finish("OK")
        elif prefix in reserved:
            await add_wiki_global.reject("前缀位于保留名字空间！请重新输入！")
        elif re.findall('\W', prefix):
            await add_wiki_global.reject("前缀含有非法字符，请重新输入！")
        else:
            state['prefix'] = prefix

    @add_wiki_global.got('prefix', _gen_prompt_template('{_prompt}'), parse_prefix)
    @add_wiki_global.handle()
    async def init_api_url(bot: Bot, event: Event, state: T_State):
        state['_prompt'] = "请输入wiki的api地址，通常形如这样：\n" + \
                           "https://www.example.org/w/api.php\n" + \
                           "https://www.example.org/api.php\n" \
                           "如果托管bot的服务器所在的国家/地区无法访问某些wiki的api，或者该wiki不提供api,你也可以回复empty来跳过输入"

    async def parse_api_url(bot: Bot, event: Event, state: T_State):
        api_url = str(event.get_message()).strip()
        if api_url.lower() == 'empty':
            state['api_url'] = ''
        elif api_url == '取消':
            await add_wiki_global.finish("OK")
        elif not re.match(r'^https?:/{2}\w.+$', api_url):
            await add_wiki_global.reject("非法url!请重新输入！")
        else:
            try:
                test_wiki = MediaWiki(url=api_url)
            except:
                await add_wiki_global.reject("无法连接到api，请重新输入！如果确认无误的话，可能是被防火墙拦截，可以输入“empty”跳过，或者“取消”来退出")
            state['api_url'] = api_url.strip().rstrip("/")

    @add_wiki_global.got('api_url', _gen_prompt_template('{_prompt}'), parse_api_url)
    @add_wiki_global.handle()
    async def init_url(bot: Bot, event: Event, state: T_State):
        state['_prompt'] = '请输入wiki的通用url，通常情况下，由该url与条目名拼接即可得到指向条目的链接，如：\n' + \
                           '中文维基百科：https://zh.wikipedia.org/wiki/\n' + \
                           '萌娘百科：https://zh.moegirl.org.cn/\n' + \
                           '另请注意：该项目不允许置空'

    async def parse_url(bot: Bot, event: Event, state: T_State):
        url = str(event.get_message()).strip()
        if url == "取消":
            await add_wiki_global.finish("OK")
        elif not re.match(r'^https?:/{2}\w.+$', url):
            await add_wiki_global.reject("非法url！请重新输入！")
        else:
            state['url'] = url.strip().rstrip("/")

    @add_wiki_global.got('url', _gen_prompt_template('{_prompt}'), parse_url)
    @add_wiki_global.handle()
    async def add_wiki_global_process(bot: Bot, event: Event, state: T_State):
        config: Config = Config(0)
        prefix: str = state["prefix"]
        api_url: str = state["api_url"]
        url: str = state["url"]
        if config.add_wiki_global(prefix, api_url, url):
            await add_wiki_global.finish(f"添加Wiki: {prefix} 成功！")
        else:
            await add_wiki_global.finish("呜……出错了……如果持续出现，请联系bot管理员进行排查")


def do_query_wikis_global(query_wikis_global: Type[Matcher]):
    @query_wikis_global.handle()
    async def _(bot: Bot, event: Event, state: T_State):
        config: Config = Config(0)
        all_data: tuple = config.list_data
        all_data_str: str = all_data[1]
        await query_wikis_global.finish(all_data_str)


def do_del_wiki_global(del_wiki_global: Type[Matcher]):
    @del_wiki_global.handle()
    async def send_list(bot: Bot, event: Event, state: T_State):
        config: Config = Config(0)
        res = "以下为全局绑定的所有wiki列表，请回复前缀来选择要删除的wiki，回复“取消”退出：\n"
        res += config.list_data[1]
        await del_wiki_global.send(message=Message(res))

    @del_wiki_global.receive()
    async def do_del(bot, event: Event, state: T_State):
        prefix = str(event.get_message()).strip()
        if prefix == "取消":
            await del_wiki_global.finish("OK")
        else:
            config: Config = Config(0)
            if config.del_wiki_global(prefix):
                await del_wiki_global.finish("删除成功")
            else:
                await del_wiki_global.finish("删除失败……请检查前缀是否有误")


def do_set_default_global(set_default_global: Type[Matcher]):
    @set_default_global.handle()
    async def send_list(bot: Bot, event: Event, state: T_State):
        config: Config = Config(0)
        res = "以下为全局wiki列表，请回复前缀来选择要设为默认的wiki，回复“取消”退出：\n"
        res += config.list_data[1]
        await set_default_global.send(message=Message(res))

    @set_default_global.receive()
    async def do_set(bot, event: Event, state: T_State):
        prefix = str(event.get_message()).strip()
        if prefix == "取消":
            await set_default_global.finish("OK")
        else:
            config: Config = Config(0)
            if config.set_default_global(prefix):
                await set_default_global.finish("设置成功")
            else:
                await set_default_global.finish("设置失败……请检查前缀是否有误")


'''
Matchers
'''
add_wiki_matcher = on_command("添加wiki", aliases={"添加Wiki", "添加WIKI"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
do_add_wiki(add_wiki_matcher)
add_wiki_global_matcher = on_command("添加全局wiki", aliases={"添加全局WIKI", "添加全局Wiki"},
                                     permission=SUPERUSER)
do_add_wiki_global(add_wiki_global_matcher)

query_wikis_matcher = on_command("wiki列表", aliases={"查看wiki", "查看Wiki", "查询wiki", "查询Wiki", "Wiki列表"}, permission=GROUP)
do_query_wikis(query_wikis_matcher)
query_wikis_global_matcher = on_command("全局wiki列表",
                                        aliases={"查看全局wiki", "查看全局Wiki", "查询全局wiki", "查询全局Wiki", "全局Wiki列表"})
do_query_wikis_global(query_wikis_global_matcher)

del_wiki_matcher = on_command("删除wiki", aliases={"删除Wiki", "删除WIKI"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
do_del_wiki(del_wiki_matcher)
del_wiki_global_matcher = on_command("删除全局WIKI", aliases={"删除全局wiki", "删除全局Wiki"}, permission=SUPERUSER)
do_del_wiki_global(del_wiki_global_matcher)

set_default_matcher = on_command("设置默认wiki", aliases={"设置默认Wiki", "设置默认WIKI"},
                                 permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
do_set_default(set_default_matcher)
set_default_global_matcher = on_command("设置全局默认wiki",
                                        aliases={"设置全局默认Wiki", "设置全局默认WIKI", "全局默认wiki", "全局默认Wiki"},
                                        permission=SUPERUSER)
do_set_default_global(set_default_global_matcher)

# class WikiInfo(BaseModel):
#     default: str
#     wikis: dict
#
#
# group_settings = on_command("Wiki设置", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
#
# @group_settings.handle()
# async def _group_settings(bot: Bot, event: GroupMessageEvent, state: T_State):
#     args = str(event.get_message()).strip()
#     if args:
#         state["command"] = args
#
# @group_settings.got("command", prompt="回复”添加Wiki“、”删除Wiki“、”Wiki列表“、“编辑Wiki”、“设置默认”或“取消”来执行相应功能")
# async def handle_command(bot: Bot, event: GroupMessageEvent, state: T_State):
#     command = str(state["command"])
#     add_list = ["添加", "添加wiki"]
#     if command == "取消":
#         await group_settings.finish("OK")
#     elif command.lower() in add_list:
#         new_wiki = []
#         await group_settings.send("请输入Wiki代号，这将用于作为条目名前区分Wiki的前缀：")
#
#     else:
#         await group_settings.reject("指令无效！请重新输入！")


# group_id = event.group_id
#
# data = await Wiki.load_group_info(group_id)
# default = data.get("default", "None")
# wikis = data.get("wikis", {})
#
# wiki_list = ""
# count = 1
# for wiki in wikis:
#     str = f"{count}. 名称：{wiki}\n" \
#           f"API地址：{wikis.get(wiki)[0]}\n" \
#           f"通用链接地址：{wikis.get(wiki)[1]}\n"
#     wiki_list += str
#     count += 1

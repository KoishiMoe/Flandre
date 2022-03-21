import re

from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Bot, utils, GroupMessageEvent, Message
from nonebot.adapters.onebot.v11.permission import GROUP

from . import config_manager
from .config import Config
from .exception import NoDefaultPrefixException, NoSuchPrefixException
from .data_source import Wiki

# 接入帮助系统
__usage__ = '使用：\n' \
            '[[前缀:条目名]] {{前缀:模板名}} ((前缀:条目名))\n' \
            '其中中括号、大括号匹配后会调用api搜索条目/模板名，如果有误，可以使用小括号方式绕过api直接生成链接\n' \
            '前缀由群管和bot超管配置，没有指定前缀或前缀无效时，会回落到默认前缀\n' \
            '查看本群wiki列表： @bot wiki列表\n' \
            '配置（带global的是全局命令，仅超管可以使用）：\n' \
            '添加：wiki.add，wiki.add.global\n' \
            '删除：wiki.delete，wiki.delete.global\n' \
            '列表：wiki.list，wiki.list.global' \
            '设置默认：wiki.default，wiki.default.global' \
            '按提示提供相应参数即可\n' \
            '注意：私聊状态下该插件仅会响应超管的命令，且仅能管理全局wiki'

__help_version__ = '0.4.0 (Flandre)'

__help_plugin_name__ = 'Wiki推送'

# 用于正则匹配的模板字符串
ARTICLE_RAW = r"&#91;&#91;(.*?)&#93;&#93;"  # adapter出于安全原因会把中括号转义，此处用于让事件响应器能正确响应事件
ARTICLE = r"\[\[(.*?)\]\]"
TEMPLATE = r"\{\{(.*?)\}\}"
RAW = r"\(\((.*?)\)\)"

# 响应器
wiki = on_regex(ARTICLE_RAW, permission=GROUP)
wiki_template = on_regex(TEMPLATE, permission=GROUP)
wiki_raw = on_regex(RAW, permission=GROUP)

# 标题列表
titles = []


@wiki.handle()
async def _wiki(bot: Bot, event: GroupMessageEvent):
    global titles
    message = str(event.message).strip()
    if message.isdigit():
        if 0 <= int(message) < len(titles) - 1:
            event.message = Message(f"[[{titles[-1]}:{titles[int(message)]}]]")
        else:
            return
    special, result = await wiki_parse(ARTICLE, False, False, bot, event)
    if special:
        titles = result[:-1]
        titles.insert(0, result[-1][1])
        titles.append(result[-1][2])
        title_list = '\n'.join([f'{i+1}.{result[i]}'for i in range(len(result) - 1)])  # 最后一个元素是特殊标记
        msg = f"{f'页面{result[-1][1]}不存在，下面是推荐的结果' if result[-1][0] else f'页面{result[-1][1]}是消歧义页面'}，" \
              f"请回复数字来选择你想要查询的条目，或者回复0来根据原标题直接生成链接：\n" \
              f"{title_list}"
        await wiki.reject(msg)
    else:
        await bot.send(event, result)
        titles = []


@wiki_template.handle()
async def _wiki_template(bot: Bot, event: GroupMessageEvent):
    global titles
    message = str(event.message).strip()
    if message.isdigit():
        if 0 <= int(message) < len(titles) - 1:
            event.message = Message(f"[[{titles[-1]}:{titles[int(message)]}]]")
        else:
            return
    special, result = await wiki_parse(TEMPLATE, True, False, bot, event)
    if special:
        titles = result[:-1]
        titles.insert(0, result[-1][1])
        titles.append(result[-1][2])
        title_list = '\n'.join([f'{i+1}.{result[i]}'for i in range(len(result) - 1)])  # 最后一个元素是特殊标记
        msg = f"{f'页面{result[-1][1]}不存在，下面是推荐的结果' if result[-1][0] else f'页面{result[-1][1]}是消歧义页面'}，" \
              f"请回复数字来选择你想要查询的条目，或者回复0来根据原标题直接生成链接：\n" \
              f"{title_list}"
        await wiki.reject(msg)
    else:
        await bot.send(event, result)
        titles = []


@wiki_raw.handle()
async def _wiki_raw(bot: Bot, event: GroupMessageEvent):
    special, result = await wiki_parse(RAW, False, True, bot, event)
    await bot.send(event, result)


# 公用方法
async def wiki_parse(pattern: str, is_template: bool, is_raw: bool, bot: Bot, event: GroupMessageEvent) -> tuple:
    msg = str(event.message).strip()
    msg = utils.unescape(msg)  # 将消息处理为正常格式，以防搜索出错
    temp_config: Config = Config(event.group_id)
    titles = re.findall(pattern, msg)
    for title in titles:
        title = str(title)
        prefix = re.match(r'\w+:|\w+：', title)
        if not prefix:
            prefix = ''
        else:
            prefix = prefix.group(0).lower().rstrip(":：")  # 删掉右侧冒号以进行匹配
            if prefix in temp_config.prefixes:
                title = re.sub(f"{prefix}:|{prefix}：", '', title, count=1, flags=re.I)  # 去除标题左侧的前缀
            else:
                prefix = ''  # 如果不在前缀列表里，视为名字空间标识，回落到默认前缀

        try:
            if title is None or title.strip() == "":
                continue
            wiki_api = temp_config.get_from_prefix(prefix)[0]
            wiki_url = temp_config.get_from_prefix(prefix)[1]

            wiki_object = Wiki(wiki_api, wiki_url)
            if not is_raw:
                special, result = await wiki_object.get_from_api(title, is_template)
            else:
                url = await wiki_object.url_parse(title)
                result = f"标题：{title}\n链接：{url}"
                special = False

            if special:
                result[-1] = list(result[-1])
                result[-1].append(prefix)  # 补充前缀，防止一会查的时候回落到默认wiki

        except NoDefaultPrefixException:
            special = False
            result = "没有找到默认前缀，请群管或bot管理员先设置默认前缀"
        except NoSuchPrefixException:
            special = False
            result = "指定的默认前缀对应的wiki不存在，请管理员检查设置"

        return special, result

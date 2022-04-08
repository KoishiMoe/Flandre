"""
提供管理功能
"""
import re
from io import BytesIO

from nonebot import Bot, on_command
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.adapters.onebot.v11.utils import unescape

from . import docs
from .file_loader import get_wordbank, save_wordbank, get_base_wordbank
from src.utils.str2img import Str2Img
from src.utils.config import RUNTIME_CONFIG as BotConfig
from .command_processor import process_command

QUIT_LIST = ["取消", "quit", "退出"]

chat_add = on_command("chat.add", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@chat_add.handle()
async def _chat_add(bot: Bot, event: MessageEvent, state: T_State):
    command_list, command_dict = process_command("chat.add", str(event.message))

    if not command_dict:
        await chat_add.finish("啊啦，你似乎没有提供参数的样子……要查看帮助吗？用chat.help命令就可以了哦～")

    state["matcher_is_regex"] = False  # 先做个标记，好确定要不要弹出下一步提示
    state["replyer_is_regex"] = False
    state["command_dict"] = command_dict

    if __str_to_bool(command_dict.get("g", False)) and str(event.user_id) not in BotConfig["superusers"]:
        await chat_add.finish("哒咩！你没有权限管理全局词库")

    try:
        new_matcher = {
            "matcher": {
                "type": command_dict["mt"],
                "probability": int(command_dict.get("o", 100)),
                "priority": int(command_dict.get("p", 10)),
                "atme": __str_to_bool(command_dict.get("a", "true"))
            },
            "reply": {
                "type": command_dict["rt"],
            }
        }
        matcher_dict = new_matcher["matcher"]
        match command_dict["mt"]:
            case "prefix":
                matcher_dict["keyword"] = __msg_restore(command_dict["k"])
            case "keyword":
                matcher_dict["keyword"] = __msg_restore(command_dict["k"])
                matcher_dict["simple_mode"] = __str_to_bool(command_dict.get("s", False))
            case "full":
                matcher_dict["text"] = __msg_restore(command_dict["mtext"])
            case "regex":
                state.pop("matcher_is_regex")
                matcher_dict["ignore_case"] = __str_to_bool(command_dict.get("mi", True))
            case _:
                raise ValueError

        replyer_dict = new_matcher["reply"]
        match command_dict["rt"]:
            case "text":
                replyer_dict["text"] = __msg_restore(command_dict["rtext"])
            case "image":
                replyer_dict["url"] = __msg_restore(command_dict["url"])
            case "voice":
                await chat_add.finish("果咩，暂时不支持在对话中添加语音回复的说……如有需要，可以用tts模式，让谷歌娘来代劳～")
            case "tts":
                replyer_dict["text"] = __msg_restore(command_dict["rtext"])
                replyer_dict["lang"] = command_dict["lang"]
            case "regex_sub":
                replyer_dict["repl"] = __msg_restore(command_dict["rtext"])
                replyer_dict["count"] = int(command_dict.get("c", 0))
                replyer_dict["ignore_case"] = __str_to_bool(command_dict.get("ri", True))
                state.pop("replyer_is_regex")
            case _:
                raise ValueError

        state["matcher"] = new_matcher

    except KeyError as e:
        await chat_add.reject(f"啊，你似乎忘了填写参数{e}……要不重新填写一下？")
    except ValueError:
        await chat_add.reject(f"似乎有参数的值不合法的说……要不重新填写一下？")


@chat_add.got("matcher_is_regex", "由于你选择了正则匹配，为了防止出错，需要单独回复用于匹配的表达式")
async def _chat_add_regex_matcher(bot: Bot, event: MessageEvent, state: T_State):
    message = str(state["matcher_is_regex"])
    if message in QUIT_LIST:
        await chat_add.finish("OK")
    elif state["matcher_is_regex"] == False:
        return
    else:
        state["matcher"]["matcher"]["regex"] = unescape(message)


@chat_add.got("replyer_is_regex", "由于你选择了正则替换回复，为了防止出错，需要单独回复正则模式字符串")
async def _chat_add_regex_replyer(bot: Bot, event: MessageEvent, state: T_State):
    message = str(state["replyer_is_regex"])
    if message in QUIT_LIST:
        await chat_add.finish("OK")
    elif state["replyer_is_regex"] == False:
        return
    else:
        state["matcher"]["replyer"]["pattern"] = unescape(message)


@chat_add.got("matcher")
async def _chat_add_finish(bot: Bot, event: MessageEvent, state: T_State):
    matcher = state["matcher"]
    if not matcher:
        await chat_add.finish("没有获取到要添加的信息，通常情况下这不应该出现……如果可以，请向开发者报告该bug")

    gid = 0 if __str_to_bool(state["command_dict"].get("g", False)) \
        else event.group_id if isinstance(event, GroupMessageEvent) else 0  # 带g参数或者私聊则视为全局，否则本群
    wordbank = await get_wordbank(gid)
    wordbank.append(matcher)
    await save_wordbank(gid, wordbank)
    await chat_add.finish("添加成功！")


chat_list = on_command("chat.list", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@chat_list.handle()
async def _chat_list(bot: Bot, event: MessageEvent, state: T_State):
    command_list, command_dict = process_command("chat.list", str(event.message))

    if __str_to_bool(command_dict.get("g", False)) and str(event.user_id) not in BotConfig["superusers"]:
        await chat_del.finish("哒咩！你没有权限管理全局词库")

    output_str = ''

    if not __str_to_bool(command_dict.get("f", False)):
        gid = 0 if __str_to_bool(command_dict.get("g", False)) \
            else event.group_id if isinstance(event, GroupMessageEvent) else 0
        wordbank = await get_wordbank(gid)
        if gid == 0:
            output_str += "注意：此处的全局词库不包括被放置在data/resources/chat中的词库。要查询基本词库的内容，请使用参数-f\n"
    else:
        wordbank = await get_base_wordbank()

    for i in range(len(wordbank)):
        match wordbank[i].get("matcher", {}).get("type", "unknown"):
            case "prefix":
                m_type = "前缀"
                value = wordbank[i].get("matcher", {}).get("keyword", "未知")
            case "keyword":
                m_type = "关键词"
                value = wordbank[i].get("matcher", {}).get("keyword", "未知")
            case "full":
                m_type = "全字"
                value = wordbank[i].get("matcher", {}).get("text", "未知")
            case "regex":
                m_type = "正则"
                value = wordbank[i].get("matcher", {}).get("regex", "未知")
            case _:
                m_type = "未知"
                value = "未知"

        output_str += f"{i+1}. 类型：{m_type}\n" \
                      f"值：{value}\n"

    image = Str2Img().gen_image(output_str.rstrip("\n"))
    output = BytesIO()

    if image:
        image.save(output, format="JPEG")
        await chat_list.finish(MessageSegment.image(output))
    else:
        await chat_list.finish("呜……出错了……")


chat_del = on_command("chat.del", permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@chat_del.handle()
async def _chat_del(bot: Bot, event: MessageEvent, state: T_State):
    command_list, command_dict = process_command("chat.del", str(event.message))

    if not command_list:
        await chat_del.finish("啊啦，你似乎没有提供要删除的序号的样子……要查看列表吗？用chat.list就可以了～")

    if __str_to_bool(command_dict.get("g", False)) and str(event.user_id) not in BotConfig["superusers"]:
        await chat_del.finish("哒咩！你没有权限管理全局词库")

    order = int(command_list[0])
    gid = 0 if __str_to_bool(command_dict.get("g", False)) \
        else event.group_id if isinstance(event, GroupMessageEvent) else 0
    wordbank = await get_wordbank(gid)
    try:
        if order > len(wordbank):
            await chat_del.finish("砰！你提供了不存在的序号！")
        wordbank.pop(order - 1)
        await save_wordbank(gid, wordbank)
        await chat_del.finish("删除成功！")
    except ValueError | IndexError:
        await chat_del.finish("呜……删除失败了……也许你提供了不存在的序号……")


chat_help = on_command("chat.help")


@chat_help.handle()
async def _chat_help(bot: Bot, event: MessageEvent, state: T_State):
    if str(event.message).strip() in ("Y", "y"):
        await chat_help.finish(docs.config_helper)

    image = Str2Img().gen_image(docs.config_helper)
    out = BytesIO()

    if image:
        image.save(out, format="JPEG")
        await chat_help.finish(MessageSegment.image(out))
    else:
        await chat_help.reject("生成图片出错了……要查看文字帮助吗？注意文字帮助很长，可能刷屏……（Y/N）")


def __str_to_bool(string: str | None | bool) -> bool:
    """
    将字符串形式的true/false转换成布尔值
    :param string: 要判断的字符串
    :return: 转换出的布尔值
    """
    return True if string in ("True", "true", "TRUE", "T", "t", True) else False


def __msg_restore(message: str) -> str:
    return unescape(message.strip("\"\'"))

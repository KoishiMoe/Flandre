"""
处理回复相关
"""
import asyncio
import re
from functools import wraps, partial
from io import BytesIO
from pathlib import Path
from random import choices

from aiohttp import ClientSession
from gtts import gTTS
from nonebot import Bot
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment
from nonebot.log import logger

from .additional import FavPostProcessOperator
from .exceptions import UnknownRestrictionTypeError, UnknownReplyTypeError
from .restrictor import FavRestrictor
from src.utils.config import ChatConfig

DATA = Path('.') / 'data' / 'resources'
DATA_ONLINE_PATH = DATA / 'online' / 'chat'
DATA_CUSTOM_PATH = DATA / 'custom' / 'chat'
STORAGE_PATH = Path('.') / 'data' / 'database' / 'chat'
HEADERS = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 '
                  'Safari/537.36'}


async def reply_handler(bot: Bot, event: MessageEvent, replyer_config: dict | list, additional_config: dict):
    if isinstance(replyer_config, dict) and replyer_config:  # 有可能传空字典过来
        match replyer_config["type"]:
            case "text":
                await __send_text(bot, event, replyer_config)
            case "image":
                await __send_image(bot, event, replyer_config)
            case "voice":
                await __send_voice(bot, event, replyer_config)
            case "tts":
                await __send_tts(bot, event, replyer_config)
            case "regex_sub":
                await __send_resub(bot, event, replyer_config)
            case "code":
                await __send_run_code(bot, event, replyer_config)
            case "restricted":
                await __handle_restriction(bot, event, replyer_config)
            case _:
                raise UnknownReplyTypeError(f"Unknown reply type {replyer_config['type']}")
    elif isinstance(replyer_config, list):
        config = choices(replyer_config, weights=[cfg.get("weight", 1) for cfg in replyer_config])[0]
        await reply_handler(bot, event, config, {})  # addition_config只需要被执行一次就行了，这里由最上层的handler执行，所以后面传空

    await __handle_additional(bot, event, additional_config)


async def __send_text(bot: Bot, event: MessageEvent, config: dict):
    resp = config.get("text", "没有定义回复消息的说……")
    resp = resp.replace("[你]", "你").replace("[我]", "我")  # TODO:增加自定义称呼

    await bot.send(event=event, message=resp)


async def __send_image(bot: Bot, event: MessageEvent, config: dict):
    image_online_path = DATA_ONLINE_PATH / 'static' / 'images'
    image_custom_path = DATA_CUSTOM_PATH / 'static' / 'images'
    image_storage_path = STORAGE_PATH / 'static' / 'images'
    filename = config.get("filename", None)
    if filename:
        if (image_storage_path / filename).is_file():
            await bot.send(event=event, message=MessageSegment.image(file=image_storage_path / filename))
        elif (image_custom_path / filename).is_file():
            await bot.send(event=event, message=MessageSegment.image(file=image_custom_path / filename))
        elif (image_online_path / filename).is_file():
            await bot.send(event=event, message=MessageSegment.image(file=image_online_path / filename))
        else:
            logger.warning(f"无法找到图片文件：{filename}，请检查词库及资源库是否完整")
    elif config.get("url", None):
        await bot.send(event=event, message=MessageSegment.image(config["url"]))
    else:
        logger.warning("词库中一个响应器的回复配置不正确：缺少图片路径或url")


async def __send_voice(bot: Bot, event: MessageEvent, config: dict):
    voice_online_path = DATA_ONLINE_PATH / 'static' / 'audio'
    voice_custom_path = DATA_CUSTOM_PATH / 'static' / 'audio'
    voice_storage_path = STORAGE_PATH / 'static' / 'audio'
    filename = config.get("filename", None)
    if filename:
        if (voice_storage_path / filename).is_file():
            await bot.send(event=event, message=MessageSegment.record(file=voice_storage_path / filename))
        elif (voice_custom_path / filename).is_file():
            await bot.send(event=event, message=MessageSegment.record(file=voice_custom_path / filename))
        elif (voice_online_path / filename).is_file():
            await bot.send(event=event, message=MessageSegment.record(file=voice_online_path / filename))
        else:
            logger.warning(f"无法找到语音文件：{filename}，请检查词库及资源库是否完整")
    else:
        logger.warning("词库中一个响应器的回复配置不正确：缺少语音路径或url")


async def __send_tts(bot: Bot, event: MessageEvent, config: dict):
    # 因为gtts使用的是同步处理……为了防止阻塞，出此下策
    def async_wrap(func):
        @wraps(func)
        async def run(*args, loop=None, executor=None, **kwargs):
            if loop is None:
                loop = asyncio.get_event_loop()
            pfunc = partial(func, *args, **kwargs)
            return await loop.run_in_executor(executor, pfunc)

        return run

    text = config.get("text", "言葉もないです").replace("[你]", "你").replace("[我]", "我")
    try:
        tts_obj = gTTS(text, lang=config.get("lang", "ja"))
        tts_exe = async_wrap(tts_obj.write_to_fp)
        output = BytesIO()
        await tts_exe(output)

        await bot.send(event=event, message=MessageSegment.record(output))
    except Exception as e:
        logger.warning(f"发送tts消息时出现了以下错误：{e}，已发送纯文本代替")
        await bot.send(event=event, message=text)


async def __send_resub(bot: Bot, event: MessageEvent, config: dict):
    if config.get("function", False) and not ChatConfig.allow_function:
        await bot.send(event=event, message="呜……这个回复包含函数，但目前函数已被禁用……如果你认为这是一个错误，请联系bot管理员")
    else:
        message = str(event.message).strip()
        reply = re.sub(
            pattern=config["pattern"],
            repl=eval(config["repl"]) if config.get("function", False) and ChatConfig.allow_function
            else config["repl"],
            string=message,
            count=config.get("count", 0),
            flags=re.I if config.get("ignore_case", True) else None
        )

        await bot.send(event=event, message=reply)


async def __send_run_code(bot: Bot, event: MessageEvent, config: dict):
    message = str(event.message).strip()
    repl = "呜……似乎没有返回值的说"

    if config.get("local", False):
        if not ChatConfig.allow_local:
            await bot.send(event=event, message="错误：管理员已禁用本地代码执行")
            return
        else:
            def fun():
                # 整成函数是为了执行完能清理一下局部变量（大概有用……吧）
                exec(config.get("code", ""))
                return str(locals().get('repl', "呜……似乎没有返回值的说……\n你是否把返回值赋值给了repl？"))
            repl = fun()
            await bot.send(event=event, message=repl)
    else:
        code = "import sys\n" \
               "message = ''.join(sys.stdin.readlines())\n" + config.get('code', "print('啊啦，没有提供代码的说……')")
        session = ClientSession(headers=HEADERS)
        try:
            resp = await session.post(
                url=f"https://glot.io/run/python?version=latest",
                json={
                        "files": [
                            {
                                "name": "main.py",
                                "content": code,
                            }
                        ],
                        "stdin": message,
                        "command": "",
                    }
            )
            resp_dict = await resp.json()
        except Exception as e:
            logger.warning(f"使用glot.io执行代码出错：{e}")
            resp_dict = {
                "error": "error",
                "stderr": "尝试使用在线服务执行代码出错"
            }
        await session.close()
        if resp_dict.get("stdout", ""):
            repl = resp_dict["stdout"]
        if resp_dict.get("error", ""):
            repl += f"\n发生了错误：{resp_dict.get('stderr')}"

        await bot.send(event=event, message=repl.strip())


async def __handle_restriction(bot: Bot, event: MessageEvent, config: dict):
    match config.get("restriction", {}).get("type", ""):
        case "fav":
            restrictor = FavRestrictor(config.get("restriction", {}).get("min_fav", 0))
            if restrictor.check(int(event.user_id)):
                await reply_handler(bot, event, config.get("allow", {}).get("reply", {}),
                                    config.get("allow", {}).get("options", {}))
            else:
                await reply_handler(bot, event, config.get("deny", {}).get("reply", {}),
                                    config.get("deny", {}).get("options", {}))
        case _:
            raise UnknownRestrictionTypeError(
                f"Unknown restriction type {config.get('restriction', {}).get('type', '')}")


async def __handle_additional(bot: Bot, event: MessageEvent, config: dict):
    if "fav" in config.keys():
        operator = FavPostProcessOperator(int(event.user_id))
        operator.execute(config["fav"])

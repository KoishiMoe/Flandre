import re

from nonebot import on_command, require, logger
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
from nonebot.adapters.onebot.v11.utils import unescape
from nonebot.params import RawCommand
from nonebot.typing import T_State

from src.utils.str2img import Str2Img
from .data_source import get_music_list

# 接入帮助系统
__usage__ = '用法：点歌 [平台] 歌名（或id,取决于平台支持度）\n' \
            '平台有 163（网易）、qq（QQ音乐），不提供的话默认网易'

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = '点歌'

# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

register("song", "点歌")

# 接入频率限制
require("ratelimit")
from ..ratelimit.config_manager import register as register_ratelimit
from ..ratelimit.rule import check_limit

register_ratelimit("song", "点歌")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag


music = on_command("点歌", aliases={"来首歌"}, rule=online("song") & gag())


@music.handle()
async def _music(bot: Bot, event: MessageEvent, state: T_State, raw_command: str = RawCommand()):
    songs_list = []
    if not await check_limit(bot, event, "song", False):
        await music.finish("好歌要一首一首听哦，过一会再来吧～")

    msg = unescape(str(event.message).strip().removeprefix(raw_command).strip())
    if "163.com" in msg:
        if "m/song/" in msg or "#/song/" in msg:
            songid = re.findall(r"song/(\d+)", msg)
        else:
            songid = re.findall(r"[?&]id=(\d+)", msg)
        if songid:
            state["source"] = "163"
            state["choice"] = "1"
            songs_list = [{"id": songid[0]}]
            state["song_list"] = songs_list

            state["keyword"] = "##Dummy##"

    if not songs_list:
        param_list = msg.split(maxsplit=1)
        if not param_list:
            return
        if len(param_list) == 1:
            keyword = param_list[0]
            source = "163"
        else:
            if param_list[0] in ("QQ", "qq", "q", "Q", "Q音", "q音", "qq音乐", "QQ音乐"):
                source = "qq"
                keyword = param_list[1]
            elif param_list[0] in ("163", "netease", "wyy", "wy", "网易云", "网抑云", "网易", "网抑"):
                source = "163"
                keyword = param_list[1]
            else:
                source = "163"
                keyword = param_list[0] + " " + param_list[1]

        state["keyword"] = keyword
        state["source"] = source


@music.got("keyword", "啊，歌名呢～")
async def _search_music(bot: Bot, event: MessageEvent, state: T_State):
    if state.get("song_list"):
        return
    keyword = str(state.get("keyword"))
    source = state.get("source") or "163"
    songs_list = await get_music_list(keyword, source)

    if not songs_list:
        await music.finish("啊，没找到你要点的歌呢……换个关键词试试，或者直接使用歌曲id吧～")
    elif len(songs_list) == 1:
        state["choice"] = "1"
    else:
        output = ""
        for i in range(len(songs_list)):
            song = songs_list[i]
            output += f"{i + 1}. {song.get('name')} —— {song.get('artist')}\n"
        if len(output) > 200:
            output = Str2Img().gen_message(output)

        await bot.send(event, output)
    state["source"] = source
    state["song_list"] = songs_list


@music.got("choice", "从上面选一首吧，回复序号即可，或者发送“取消”来退出～")
async def _send_music(bot: Bot, event: MessageEvent, state: T_State):
    choice = str(state["choice"]).strip()
    song_list = state["song_list"]
    if not choice.isdigit():
        return
    elif not (1 <= int(choice) <= len(song_list)):
        await music.reject(f"选择数字应该在 1～{len(song_list)} 之间，请重新选择！")

    choice = int(choice)
    song = song_list[choice - 1]

    match state["source"]:
        case "163":
            msg = MessageSegment.music("163", song["id"])
        case "qq":
            msg = MessageSegment.music("qq", song["id"])
        case _:
            logger.warning(f"未知的音乐平台：{state['source']}，通常情况下这不应该出现")
            return

    await check_limit(bot, event, "song", True)
    await music.finish(msg)

import asyncio
import re
from io import BytesIO
from random import randint
from sys import exc_info
from time import localtime, strftime
from traceback import format_exc

from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Bot, Event, PrivateMessageEvent, MessageSegment
from nonebot.matcher import Matcher
from nonebot.message import run_postprocessor
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from src.utils.config import BotConfig
from src.utils.str2img import Str2Img
from .sqlite import sqlite_pool


@run_postprocessor
async def exception_hook(matcher: Matcher, exception: Exception | None, bot: Bot, event: Event, state: T_State):
    if not exception:
        return

    try:
        raise exception
    except Exception as e:
        exc_type, exc_value = exc_info()[0:2]
        trace = format_exc()
        exc_time = strftime("%Y-%m-%d %H:%M:%S", localtime())

    exc_type = re.search(r"<class '(.+)'>", str(exc_type), flags=re.I)
    if exc_type:
        exc_type = str(exc_type.group(1))
    exc_value = str(exc_value)

    prompt = ""
    (track_id, ) = await sqlite_pool.fetch_one("select max(track_id) from exceptions")
    if track_id:
        track_id = int(track_id) + 1
    else:
        track_id = 100000  # QQ里6位以上的数字可以点击复制

    # 话说真的有人能用到上限吗（（（
    if len(str(track_id)) == 11:
        prompt += "警告：当前追踪日志数量较多，建议在查看完需要的日志后，使用 track clear 清理日志，以免造成异常\n"
    if len(str(track_id)) > 11:
        prompt += "警告：当前track_id长度超限，已开始覆盖旧id，请尽快使用 track clear 清理日志\n"
        track_id = randint(100000, 9999999999)

    await sqlite_pool.execute("insert into exceptions(track_id, exc_time, exc_type, exc_value, trace) "
                              "values (:track_id, :exc_time, :exc_type, :exc_value, :trace)",
                              {
                                  "track_id": str(track_id),
                                  "exc_time": exc_time,
                                  "exc_type": exc_type,
                                  "exc_value": exc_value,
                                  "trace": trace
                              })

    logger.info(f"记录了一条错误信息，追踪码：{track_id}")
    prompt += f"那个……我似乎遇上了一些问题……╥﹏╥...\n" \
              f"下面的信息也许能帮助主人来进行排查ヽ(*。>Д<)o゜\n" \
              f"追踪码：{track_id}\n" \
              f"发生时间：{exc_time}\n" \
              f"错误类型：{exc_type}\n" \
              f"Tip:使用 track 可以获得最近一条错误信息，使用 track 追踪码 可以获得错误的具体信息，使用 track clear 可以清空日志"

    for su in BotConfig.superusers:
        await bot.send_private_msg(user_id=su, message=prompt)
        await asyncio.sleep(1)


track = on_command("track", aliases={"追踪"}, permission=SUPERUSER)


@track.handle()
async def _track(bot: Bot, event: PrivateMessageEvent, raw_command: str = RawCommand()):
    param = str(event.message).strip().removeprefix(raw_command).strip()

    if not param:
        param = "0"
    elif param in ("clear", "清空"):
        await __clear()
        await track.finish("清空错误记录成功！\n"
                           "Tip:此处清空的只是用于错误报告的数据库，日志文件仍将被保留<(￣︶￣)>")
    elif not (param.isdigit() and (100000 <= int(param) < 100000000000)):
        await track.finish("你似乎提供了无效的追踪码╮(╯▽╰)╭")

    track_id = int(param)

    log = await __get_log(track_id) or "啊啦，没有找到该追踪码的样子……"
    await track.finish(log)


async def __clear():
    await sqlite_pool.execute("delete from exceptions")


async def __get_log(track_id: int) -> str | MessageSegment | None:
    if not track_id:  # track_id=0，即获取最新；当然如果id超限了这个就不是最新了，不过……应该不会真有人用到超限吧…………
        (track_id, ) = await sqlite_pool.fetch_one("select max(track_id) from exceptions")
    result = await sqlite_pool.fetch_one("select exc_time, exc_type, exc_value, trace "
                                         "from exceptions where track_id=:track_id",
                                         {"track_id": str(track_id)})
    if not result:
        return None
    exc_time, exc_type, exc_value, trace = result
    output = f"发生时间：{exc_time}\n" \
             f"错误类型：{exc_type}\n" \
             f"错误信息：{exc_value}\n" \
             f"traceback：\n{trace}"

    if len(output) > 200:
        try:
            max_len = min(max(int(max([len(i) for i in output.split("\n")]) / 2) * 40 + 300, 1080), 65500)
            # 40是默认字体大小，1080是默认宽度，300是留给边框的宽度，宽度太小会出问题
            # traceback自带格式，图片暴力切割会影响查看，所以提前计算下长度
            out_img = BytesIO()
            img = Str2Img(width=max_len).gen_image(output)
            img.save(out_img, format="JPEG")
            output = MessageSegment.image(out_img)
        except Exception as e:
            err = f"生成错误报告图片时发生了错误：{repr(e)}"
            logger.warning(err)
            output = err + "\n" + output

    return output

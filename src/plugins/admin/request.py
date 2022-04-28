import asyncio
import os
from datetime import datetime
from io import BytesIO
from json import loads, dumps
from pathlib import Path

from nonebot import on_request, on_notice, on_command
from nonebot.adapters.onebot.v11 import Bot, FriendRequestEvent, GroupRequestEvent, \
    FriendAddNoticeEvent, MessageEvent, MessageSegment
from nonebot.log import logger
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER

from src.utils.config import BotConfig
from src.utils.str2img import Str2Img

path = Path(".") / "data" / "database" / "admin"
file = path / "request.json"


req = on_request()


@req.handle()
async def _catch(bot: Bot, event: FriendRequestEvent | GroupRequestEvent):
    data = load_file()
    friend = isinstance(event, FriendRequestEvent)
    data[len(data)] = {
        "user": event.user_id,
        "friend": friend,
        "code": event.flag,
        "comment": event.comment,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "group": event.group_id if not friend else '',
        "status": "waiting",
    }
    notice = f"啊啦，{'有人想和我成为好朋友耶～'if friend else '有人想邀请我去群里玩耶～'}\n" \
             f"申请码：{len(data) - 1}\n" \
             f"申请人：{event.user_id}\n" \
             f"申请信息：{event.comment}"
    if not friend:
        notice += f"\n群号：{event.group_id}"

    save_file(data)
    for su in BotConfig.superusers:
        await bot.send_private_msg(user_id=su, message=notice)
        await asyncio.sleep(1)

friend_add = on_notice()


@friend_add.handle()
async def _friend_add(bot: Bot, event: FriendAddNoticeEvent):
    notice = f"嘿！{event.user_id}刚刚和咱成为了朋友欸～"
    for su in BotConfig.superusers:
        await bot.send_private_msg(user_id=su, message=notice)
        await asyncio.sleep(1)


handle_request = on_command("agree", aliases={"同意", "approve", "refuse", "拒绝", "请求列表", "request", "requests"},
                            permission=SUPERUSER)


@handle_request.handle()
async def _handle_request(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    data = load_file()
    if raw_command in ("请求列表", "request", "requests"):
        if str(event.message).removeprefix(raw_command).strip() == "clear":
            save_file({})
            await handle_request.finish("清空申请列表成功！")
        resp = "Tip: 每个条目前的序号即为申请码"
        for k, v in data.items():
            if v["status"] == "waiting":
                resp += f"\n{k}.申请人：{v['user']}\n" \
                        f"类型：{'好友申请' if v['friend'] else '群聊邀请'}\n" \
                        f"申请信息：{v['comment']}\n" \
                        f"申请时间：{v['time']}"
                if not v['friend']:
                    resp += f"\n群号：{v['group']}"

        if len(resp) > 150:
            out_img = BytesIO()
            out = Str2Img().gen_image(resp)
            out.save(out_img, format="JPEG")
            resp = MessageSegment.image(out_img)
        await handle_request.finish(resp)
    else:
        agree = raw_command in ("agree", "同意", "approve")
        code = str(event.message).removeprefix(raw_command).strip()

        if not (code and code.isdigit()):
            await handle_request.finish("参数错误，申请码应为数字")
        if data[code]["status"] != "waiting":
            await handle_request.finish("这个申请似乎已经被处理过了……")
        try:
            if data[code]["friend"]:
                await bot.set_friend_add_request(flag=data[code]["code"], approve=agree)
            else:
                await bot.set_group_add_request(flag=data[code]["code"], sub_type="invite", approve=agree)
            data[code]["status"] = "approved" if agree else "rejected"
            save_file(data)
            await bot.send(event, "处理成功（*＾-＾*）")  # 不用finish是因为会抛出FinishedException,会被捕获……
        except Exception as e:
            logger.warning(f"处理请求{code}时出现了错误:{e}")
            await handle_request.finish("呜……请求处理出错了……也许需要主人来手动处理了(。﹏。)")


def load_file() -> dict:
    os.makedirs(path, exist_ok=True)
    if not file.is_file():
        with open(file, "w", encoding="utf-8") as w:
            w.write(dumps({}, indent=2))

    data = loads(file.read_bytes())

    return data


def save_file(data: dict):
    with open(file, "w", encoding="utf-8") as w:
        w.write(dumps(data, indent=2))

import asyncio
import os
from io import BytesIO
from json import loads, dumps
from pathlib import Path
from time import localtime, strftime

from nonebot import on_request, on_notice, on_command
from nonebot.adapters.onebot.v11 import Bot, FriendRequestEvent, GroupRequestEvent, \
    FriendAddNoticeEvent, MessageEvent, MessageSegment, GroupIncreaseNoticeEvent
from nonebot.log import logger
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from src.utils.config import BotConfig
from src.utils.str2img import Str2Img
from .ban import get_banned_users
from .trust import get_trusted_users

path = Path(".") / "data" / "database" / "admin"
FILE = path / "request.json"
GROUP_RECORD = path / "groups.json"


req = on_request()


@req.handle()
async def _catch(bot: Bot, event: FriendRequestEvent | GroupRequestEvent):
    if isinstance(event, GroupRequestEvent) and event.sub_type != "invite":
        return
    data = load_file(file=FILE)
    friend = isinstance(event, FriendRequestEvent)
    apply_code = len(data)
    data[apply_code] = {
        "user": event.user_id,
        "friend": friend,
        "code": event.flag,
        "comment": event.comment,
        "time": strftime('%Y-%m-%d %H:%M:%S', localtime(event.time)),
        "group": event.group_id if not friend else '',
        "status": "waiting",
    }
    notice = f"啊啦，{'有人想和我成为好朋友耶～'if friend else '有人想邀请我去群里玩耶～'}\n" \
             f"申请码：{apply_code}\n" \
             f"申请人：{event.user_id}\n" \
             f"申请信息：{event.comment}\n" \
             f"申请时间：{strftime('%Y-%m-%d %H:%M:%S', localtime(event.time))}"
    if not friend:
        notice += f"\n群号：{event.group_id}"

    # 检查用户是否被信任
    if await SUPERUSER(bot, event) or str(event.user_id) in BotConfig.superusers \
            or str(event.user_id) in get_trusted_users():
        data[apply_code]["status"] = "approved"
        if friend:
            await bot.set_friend_add_request(flag=event.flag, approve=True)
        else:
            await bot.set_group_add_request(flag=event.flag, sub_type="invite", approve=True)
        notice = f"哒！用户{event.user_id}尝试{'和咱加好友' if friend else f'邀请咱加入群{event.group_id}'}\n" \
                 f"并且咱按照主人的要求，同意了TA的请求ｍ(o・ω・o)ｍ"

    # 检查用户封禁状态
    if data[apply_code]["status"] != "approved":
        reject = str(event.user_id) in get_banned_users(is_group=False)
        if not friend:
            reject = str(event.group_id) in get_banned_users(is_group=True) or reject
        if reject:
            data[apply_code]["status"] = "rejected"
            if friend:
                await bot.set_friend_add_request(flag=event.flag, approve=False)
            else:
                await bot.set_group_add_request(flag=event.flag, sub_type="invite", approve=False)
            notice = f"砰！用户{event.user_id}尝试{'和咱加好友' if friend else f'邀请咱加入群{event.group_id}'}\n" \
                     f"不过咱按照主人之前的要求，拒绝了TA<(￣ˇ￣)/"

    save_file(data, file=FILE)
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


group_add = on_notice(rule=to_me())


@group_add.handle()
async def _group_add(bot: Bot, event: GroupIncreaseNoticeEvent):
    notice = f"群{event.group_id}的管理员{event.operator_id}成功邀请了咱去TA的群玩了～" if event.sub_type == 'invite' \
        else f"有人成功邀请咱去群{event.group_id}里去玩了～"
    notice = "嘿！" + notice + "\n如果主人之前没有批准的话，可能是坏企鹅自作主张了，主人可以向我说 leave 来让我快速离开最新加入的群( ╯▽╰)"

    group_records = load_file(GROUP_RECORD, is_list=True)
    group_records.append(str(event.group_id))
    save_file(group_records, GROUP_RECORD)

    for su in BotConfig.superusers:
        await bot.send_private_msg(user_id=su, message=notice)
        await asyncio.sleep(1)


handle_request = on_command("agree", aliases={"同意", "approve", "refuse", "拒绝", "请求列表", "request", "requests"},
                            permission=SUPERUSER)


@handle_request.handle()
async def _handle_request(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    data = load_file(file=FILE)
    if raw_command in ("请求列表", "request", "requests"):
        if str(event.message).removeprefix(raw_command).strip() == "clear":
            save_file({}, file=FILE)
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
            save_file(data, file=FILE)
            await bot.send(event, "处理成功（*＾-＾*）")  # 不用finish是因为会抛出FinishedException,会被捕获……
        except Exception as e:
            logger.warning(f"处理请求{code}时出现了错误:{e}")
            await handle_request.finish("呜……请求处理出错了……也许需要主人来手动处理了(。﹏。)")


def load_file(file, is_list: bool = FILE) -> dict | list:
    os.makedirs(path, exist_ok=True)
    if not file.is_file():
        with open(file, "w", encoding="utf-8") as w:
            w.write(dumps({} if not is_list else [], indent=2))

    data = loads(file.read_bytes())

    return data


def save_file(data: dict | list, file):
    with open(file, "w", encoding="utf-8") as w:
        w.write(dumps(data, indent=2))

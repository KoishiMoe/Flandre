"""
删好友与退群
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment, GroupMessageEvent
from nonebot.log import logger
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State

from src.utils.str2img import Str2Img
from .request import GROUP_RECORD, load_file, save_file

list_friends = on_command("friend", aliases={"friends", "好友列表"}, rule=to_me(), permission=SUPERUSER,
                          state={"group": False})
list_groups = on_command("groups", aliases={"group", "群列表"}, rule=to_me(), permission=SUPERUSER,
                         state={"group": True})


@list_friends.handle()
@list_groups.handle()
async def _friends(bot: Bot, event: MessageEvent, state: T_State):
    is_group = state["group"]
    friends_list = await bot.get_friend_list() if not is_group else await bot.get_group_list()
    friends = ""
    if not is_group:
        for i in range(len(friends_list)):
            friend = friends_list[i]
            friends += f"{i + 1}. QQ：{friend.get('user_id')} 昵称：{friend.get('nickname')}\n"
    else:
        for i in range(len(friends_list)):
            friend = friends_list[i]
            friends += f"{i + 1}. 群号：{friend.get('group_id')} 群名：{friend.get('group_name')}\n"
    if friends:
        if isinstance(event, GroupMessageEvent) and len(friends) > 200:  # 私聊就不防刷屏了，文字复制更方便些
            await list_friends.finish(MessageSegment.image(Str2Img().gen_bytes(friends)))
        else:
            await list_friends.finish(friends)
    else:
        await list_friends.finish(f"呜，我似乎还没有{'朋友' if not is_group else '加入任何群'}的样子╥﹏╥...")


delete = on_command("delete", aliases={"删除", "删除好友", "删好友", "友尽"}, rule=to_me(), permission=SUPERUSER,
                    state={"friend": True})
leave = on_command("leave", aliases={"退出", "退群"}, rule=to_me(), permission=SUPERUSER, state={"friend": False})


@delete.handle()
@leave.handle()
async def _delete(bot: Bot, event: MessageEvent, state: T_State, raw_command: str = RawCommand()):
    friend: bool = state["friend"]
    param_list = str(event.message).strip().removeprefix(raw_command).strip().split()
    if friend:
        if not param_list:
            await delete.finish("请在命令后提供要删除的好友的QQ号")
        else:
            success, fail = set(), set()
            for user in set(param_list):
                if user.isdigit():
                    try:
                        await bot.call_api("delete_friend", **{
                            "user_id": int(user),
                        })  # adapter似乎没有提供这个api，并且onebot标准也没有，应该是go-cqhttp专属；
                        # 另外文档里这里是friend_id，但是测试发现会提示用户不存在，user_id就行……闹鬼了
                        success.add(user)
                    except Exception as e:
                        logger.warning(f"删除好友{user}时发生了错误：{e}")
                        fail.add(user)
                else:
                    fail.add(user)
            report = f"操作完成，有{len(success)}个成功，{len(fail)}个失败"
            if fail:
                report += "\n失败的有：" + "，".join(fail)
            await delete.finish(report)
    else:
        group_record: list = load_file(GROUP_RECORD)
        force = bool({"-f", "-F", "f", "F"}.intersection(set(param_list)))
        param_list = set(param_list).difference({"-f", "-F", "f", "F"})
        if not param_list:  # 没给群号，删最近的
            if group_record:
                gid = group_record.pop(-1)
                await bot.set_group_leave(group_id=int(gid), is_dismiss=force)
                save_file(group_record, GROUP_RECORD)
                await leave.finish(f"成功退出群{gid}")
            else:
                await leave.finish("啊啦，我这边似乎没有加群记录的样子……要不手动指定个群号再试试？")
        else:
            success, fail = [], []
            for group in param_list:
                if group.isdigit():
                    try:
                        await bot.set_group_leave(group_id=int(group), is_dismiss=force)
                        try:
                            group_record.remove(group)
                        except ValueError:
                            pass  # 可能记录里没有，无伤大雅
                        success.append(group)
                    except Exception as e:
                        logger.warning(f"退出群{group}时发生了错误：{e}")
                        fail.append(group)
                else:
                    fail.append(group)
            save_file(group_record, GROUP_RECORD)

            report = f"操作完成，有{len(success)}个成功，{len(fail)}个失败"
            if fail:
                report += "\n失败的有：" + "，".join(fail)
            await leave.finish(report)

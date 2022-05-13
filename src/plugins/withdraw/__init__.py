from typing import Any, Dict
from typing import Callable

from nonebot import on_command, on_notice
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, PrivateMessageEvent, GroupRecallNoticeEvent, \
    MessageEvent
from nonebot.log import logger
from nonebot.plugin import require
from nonebot.rule import Rule
from nonebot.rule import to_me
from nonebot.typing import T_CalledAPIHook
from nonebot.params import RawCommand

from src.utils.config import WithdrawConfig

# 接入服务管理器
register: Callable = require("service").register
online: Callable = require("service").online

register("withdraw", "撤回bot消息（不建议禁用）")

# 从 https://github.com/MeetWq/nonebot-plugin-withdraw 抄了大量代码
# 原项目LICENSE：https://github.com/MeetWq/nonebot-plugin-withdraw/blob/main/LICENSE

# 接入帮助系统
__usage__ = '撤回一条：\n' \
            '   方法一：@bot 撤回 [消息id（最后一条可以省略）]\n' \
            '   方法二：向相应的消息回复”撤回“\n' \
            '批量撤回：\n' \
            '   从最后一条开始批量撤回消息：@bot 撤回 +[消息数量 -1]\n' \
            '   从某条开始撤回指定数量消息：@bot 撤回 起始消息id+要增加的数量\n' \
            '   撤回指定范围消息：@bot 撤回 起始消息id-结束消息id\n' \
            '   撤回从最新一条到指定消息：@bot 撤回 -结束消息id\n' \
            '   撤回从指定条到能撤回的最旧一条：@bot 撤回 起始消息id-\n' \
            '注意：消息id是从最新一条消息开始数，其中最新一条消息的id为0'

__help_version__ = '0.1.2 (Flandre)'

__help_plugin_name__ = '撤回'

msg_ids = {}
max_size = WithdrawConfig.max_withdraw_num


def get_key(msg_type, mid):
    return f'{msg_type}_{mid}'


@Bot.on_called_api
async def save_msg_id(bot: Bot, e: Exception, api: str, data: Dict[str, Any], result: Any) -> T_CalledAPIHook | None:
    try:
        if api == 'send_msg':
            msg_type = data['message_type']
            uid = data['group_id'] if msg_type == 'group' else data['user_id']
        elif api == 'send_private_msg':
            msg_type = 'private'
            uid = data['user_id']
        elif api == 'send_group_msg':
            msg_type = 'group'
            uid = data['group_id']
        else:
            return
        key = get_key(msg_type, uid)
        msg_id = result['message_id']

        if key not in msg_ids:
            msg_ids[key] = []
        msg_ids[key].append(msg_id)
        if len(msg_ids[key]) > max_size:
            msg_ids[key].pop(0)
    except Exception as e:
        logger.warning(f"记录消息列表时发生了错误，可能影响该条消息的撤回：\n{e}")


withdraw = on_command('withdraw', aliases={'撤回', 'recall'}, rule=to_me() & online("withdraw"), priority=1)


@withdraw.handle()
async def _(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    if isinstance(event, GroupMessageEvent):
        msg_type = 'group'
        uid = event.group_id
    elif isinstance(event, PrivateMessageEvent):
        msg_type = 'private'
        uid = event.user_id
    else:
        return
    key = get_key(msg_type, uid)

    if event.reply:
        msg_id = event.reply.message_id
        try:
            await bot.delete_msg(message_id=msg_id)
            return
        except Exception:
            await withdraw.finish('撤回失败，可能已超时')

    msg = str(event.message).strip().removeprefix(raw_command).lstrip()
    if not msg:
        nums = [0]
    else:
        params = msg.split()
        nums = set()
        for param in params:
            if param.isdigit() and 0 <= int(param) < len(msg_ids[key]):
                nums.add(int(param))
            elif "-" in param:
                if param.startswith("-"):
                    end = param.lstrip("-")
                    if end.isdigit():
                        nums = nums.union(range(int(end)))
                elif param.endswith("-"):
                    start = param.rstrip("-")
                    if start.isdigit():
                        nums = nums.union(range(int(start), len(msg_ids[key])))
                else:
                    split = param.split("-")
                    if len(split) == 2 and split[0].isdigit() and split[1].isdigit():
                        start, end = int(split[0]), int(split[1])
                        nums = nums.union(range(start, end + 1))
            elif "+" in param:
                if param.startswith("+"):
                    end = param.lstrip("+")
                    if end.isdigit():
                        nums = nums.union(range(int(end) + 1))
                else:
                    split = param.split("+")
                    if len(split) == 2 and split[0].isdigit() and split[1].isdigit():
                        start, end = int(split[0]), int(split[1])
                        nums = nums.union(range(start, start + end + 1))

    try:
        msg_ids_bak = msg_ids[key][:]  # 备份原列表，以防pop后索引位置出错
        for num in nums:
            idx = -num - 1
            await bot.delete_msg(message_id=msg_ids_bak[idx])
            msg_ids[key].remove(msg_ids_bak[idx])
    except Exception as e:
        await withdraw.finish('撤回失败，可能已超时')


async def _group_recall(bot: Bot, event: Event) -> bool:
    if isinstance(event, GroupRecallNoticeEvent) and str(event.user_id) == str(bot.self_id):
        return True
    return False


withdraw_notice = on_notice(Rule(_group_recall) & online("withdraw"))


@withdraw_notice.handle()
async def _(event: GroupRecallNoticeEvent):
    msg_id = int(event.message_id)
    gid = event.group_id
    key = get_key('group', gid)
    if key in msg_ids and msg_id in msg_ids[key]:
        msg_ids[key].remove(msg_id)

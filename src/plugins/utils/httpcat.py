from nonebot.adapters.cqhttp import Bot, MessageEvent, MessageSegment, Message
from nonebot import on_command
from nonebot.typing import T_State

http_cat = on_command("httpcat")

@http_cat.handle()
async def _http_cat(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.message).strip()
    if msg.isnumeric() and len(msg) == 3:
        image = MessageSegment.image(f'https://http.cat/{msg}')
        await bot.send(event, message=Message(image))
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment, Message
from nonebot import on_command

http_cat = on_command("httpcat")


@http_cat.handle()
async def _http_cat(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()[7:].lstrip()
    if msg.isnumeric() and len(msg) == 3:
        image = MessageSegment.image(f'https://http.cat/{msg}')
        await bot.send(event, message=Message(image))

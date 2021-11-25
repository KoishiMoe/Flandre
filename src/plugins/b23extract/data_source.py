from bilibili_api import video, Credential, exceptions
from nonebot.adapters.cqhttp import MessageSegment
from nonebot.log import logger


class Extract:
    @staticmethod
    async def av_parse(avid: int, credential: Credential = None):
        vid = video.Video(aid=avid)
        try:
            info = await vid.get_info()
        except exceptions.ResponseCodeException as e:
            logger.warning(e)
            return str(e)
        except exceptions.NetworkException as e:
            logger.error(e)
            return "获取稿件信息失败：网络错误"
        except exceptions as e:
            logger.error(e)
            return "获取稿件信息失败：未知错误"

        tname = info.get("tname", "未知分类")
        pic = info.get("pic", "")
        title = info.get("title", "未知标题")
        desc = info.get("desc", "")
        desc = desc if len(desc) <= 100 else desc[:100] + "……"  # 防止长简介刷屏

        if pic:
            message = MessageSegment.image(pic, cache=True, timeout=1000)
        else:
            message = ""
        message += f"\nAV{avid}\n" \
                   f"标题：{title}\n" \
                   f"分类：{tname}\n" \
                   f"简介：{desc}"

        return message

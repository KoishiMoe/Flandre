import os
from pathlib import Path

from aiofile import Writer, AIOFile
from aiohttp import ClientSession, ClientTimeout
from nonebot.log import logger

DATA = Path('.') / 'data' / 'resources'
DATA_ONLINE_PATH = DATA / 'online' / 'b23extract'
DATA_CUSTOM_PATH = DATA / 'custom' / 'b23extract'

DATA_URL = "https://raw.githubusercontent.com/KoishiStudio/Flandre-resources/b23extract/"
USER_AGENT: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'


async def get_font_path():
    custom_font = DATA_CUSTOM_PATH / 'font.ttf'
    online_font = DATA_ONLINE_PATH / 'font.ttf'

    if not DATA.is_dir():
        os.makedirs(DATA)
    if not DATA_CUSTOM_PATH.is_dir():
        os.makedirs(DATA_CUSTOM_PATH)
    if not DATA_ONLINE_PATH.is_dir():
        os.makedirs(DATA_ONLINE_PATH)
    if not custom_font.exists():
        if online_font.exists():
            font = online_font
        else:
            logger.info("未找到字体文件，正在尝试下载……")
            try:
                await download_file('font.ttf', online_font)
                font = online_font
            except Exception as e:
                logger.error(f"下载字体文件失败：{e}")
                raise FileDownloadError(e)
    else:
        font = custom_font

    return font


async def get_img_path():
    custom_header = DATA_CUSTOM_PATH / 'header.png'
    custom_footer = DATA_CUSTOM_PATH / 'footer.png'
    online_header = DATA_ONLINE_PATH / 'header.png'
    online_footer = DATA_ONLINE_PATH / 'footer.png'

    # 上面已经检测过了，这里就不做重复工作了……
    if not custom_header.exists():
        if online_header.exists() and online_footer.exists():
            header, footer = online_header, online_footer
        else:
            logger.info("未找到图片模板，正在尝试下载……")
            try:
                await download_file('header.png', online_header)
                await download_file('footer.png', online_footer)
                header, footer = online_header, online_footer
            except Exception as e:
                logger.error(f"下载图片失败：{e}")
                raise FileDownloadError(e)
    else:
        header, footer = custom_header, custom_footer

    return header, footer


async def download_file(filename: str, filepath: Path):
    async with ClientSession(headers={'User-Agent': USER_AGENT}) as session:
        async with session.get(f"{DATA_URL}{filename}", timeout=ClientTimeout(total=30)) as resp:
            async with AIOFile(filepath, 'wb') as f:
                writer = Writer(f)
                result = await resp.read()
                await writer(result)
                await f.fsync()


class FileDownloadError(Exception):
    pass

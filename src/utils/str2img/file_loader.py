import os
from pathlib import Path

from aiofile import Writer, AIOFile
from aiohttp import ClientSession, ClientTimeout
from nonebot.log import logger

DATA = Path('.') / 'data' / 'resources'
DATA_ONLINE_PATH = DATA / 'online' / 'str2img'
DATA_CUSTOM_PATH = DATA / 'custom' / 'str2img'

DATA_URL = "https://github.com/KoishiMoe/Flandre-resources/raw/main/str2img/"
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
                logger.error(f"下载字体文件失败：{e}\n"
                             f"如果无法自动下载，请前往{DATA_URL}手动下载，并将其置于./data/resources/online/str2img/中")
                raise FileDownloadError(e)
    else:
        font = custom_font

    return font


async def download_file(filename: str, filepath: Path):
    async with ClientSession(headers={'User-Agent': USER_AGENT}) as session:
        async with session.get(f"{DATA_URL}{filename}", timeout=ClientTimeout(total=120)) as resp:
            async with AIOFile(filepath, 'wb') as f:
                writer = Writer(f)
                result = await resp.read()
                await writer(result)
                await f.fsync()


class FileDownloadError(Exception):
    pass

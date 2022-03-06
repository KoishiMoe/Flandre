from PIL import Image, ImageDraw, ImageFont
from nonebot import get_driver
from wcwidth import wcwidth

from .file_loader import get_font_path, get_img_path, FileDownloadError

'''
参考了以下项目：
https://github.com/mobyw/nonebot-plugin-txt2img
https://github.com/taseikyo/txt2img
'''

driver = get_driver()

font, header, footer = '', '', ''


@driver.on_startup
async def startup():
    global font, header, footer
    font = await get_font_path()
    header, footer = await get_img_path()


class Str2Img:
    def __init__(self, font_size: int = 30, width: int = 1080):
        self.font = str(font)
        self.font_size = font_size
        self.line_space = font_size
        self.width = width

    def __wrap(self, text: str):
        max_width = int(1850 / self.font_size)
        temp_len = 0
        result = ''
        for char in text:
            result += char
            temp_len += wcwidth(char)
            if char == '\n':
                temp_len = 0
            if temp_len >= max_width:
                temp_len = 0
                result += '\n'
        result = result.rstrip()

        return result

    def gen_image(self, text: str):
        # bili_light
        border_color = (181, 180, 188)
        text_color = (74, 69, 99)
        left_text_padding = 150
        left_border_padding = 112
        head_padding = 90
        foot_padding = 973

        img_font = ImageFont.truetype(self.font, self.font_size)

        text = self.__wrap(text)

        if text.find("\n") > -1:
            text_rows = len(text.split('\n'))
        else:
            text_rows = -1

        width = self.width

        inner_height = (
                + self.font_size * text_rows
                + (text_rows - 1) * self.line_space
        )
        height = head_padding + inner_height + foot_padding

        out_img = Image.new(mode="RGB", size=(width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(out_img)

        # draw border
        draw.line([(left_border_padding, head_padding), (left_border_padding, height - foot_padding)],
                  fill=border_color, width=4)
        draw.line([(width - left_border_padding, head_padding), (width - left_border_padding, height - foot_padding)],
                  fill=border_color, width=4)

        # draw header&footer
        head_image = Image.open(header)
        foot_image = Image.open(footer)
        out_img.paste(head_image, (0, 0))
        out_img.paste(foot_image, (0, height - foot_padding))

        # draw text
        draw.text(
            (left_text_padding, head_padding), text, font=img_font, fill=text_color, spacing=self.line_space
        )

        return out_img

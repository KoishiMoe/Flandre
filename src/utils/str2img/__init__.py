from io import BytesIO

import qrcode
from PIL import Image, ImageDraw, ImageFont
from nonebot import get_driver
from wcwidth import wcwidth

from .file_loader import get_font_path, FileDownloadError

# 参考了以下项目：
# https://github.com/mobyw/nonebot-plugin-txt2img
# https://github.com/taseikyo/txt2img

driver = get_driver()

font = ''


@driver.on_startup
async def startup():
    global font
    font = await get_font_path()


class Str2Img:
    def __init__(self,
                 font_size: int = 40, line_space: int = None, width: int = 1080, qrcode_size: int = 150,
                 font_color: tuple = (70, 70, 100), border_color: tuple = (180, 180, 180),
                 background_color: tuple = (255, 255, 255), qrcode_color: tuple = (70, 70, 100),
                 border_horizontal_padding: int = 100, border_vertical_padding: int = 50,
                 text_horizontal_padding: int = 50, text_vertical_padding: int = 40,
                 head_max_width: int = 1080, head_max_height: int = 1080
                 ):
        self.font = str(font)
        self.font_size = font_size
        self.line_space = font_size if not line_space else line_space
        self.width = width
        self.qrcode_size = qrcode_size
        self.font_color = font_color
        self.border_color = border_color
        self.bg_color = background_color
        self.qrcode_color = qrcode_color
        self.border_horizontal_padding = border_horizontal_padding
        self.border_vertical_padding = border_vertical_padding
        self.text_horizontal_padding = text_horizontal_padding
        self.text_vertical_padding = text_vertical_padding
        self.head_max_width = head_max_width
        self.head_max_height = head_max_height

    def __wrap(self, text: str):
        max_width = int((self.width -
                         2 * (self.border_horizontal_padding + self.text_horizontal_padding)) / self.font_size)
        temp_len = 0
        result = ''
        for char in text:
            result += char
            char_len = wcwidth(char)
            temp_len += char_len / 2 if char_len > 0 else char_len  # 更纱黑体2英文字符=1中文字符
            if char == '\n':
                temp_len = 0
            if temp_len >= max_width:
                temp_len = 0
                result += '\n'
        result = result.rstrip().lstrip('\n')  # 删除左侧空行

        return result

    def __resize_head(self, head_pic: BytesIO):
        head = Image.open(head_pic)
        x, y = head.size
        if x / y >= 1:
            tmp_y = int(self.head_max_width * (y / x))
            head = head.resize((self.head_max_width, tmp_y), Image.ANTIALIAS)
            height = tmp_y
        else:
            tmp_x = int(self.head_max_height * (x / y))
            head = head.resize((tmp_x, self.head_max_height), Image.ANTIALIAS)
            height = self.head_max_height

        return head, height

    def __gen_qrcode(self, qrc: str, height: int):
        qr = qrcode.QRCode()
        qr.add_data(qrc)
        qr.make(fit=True)
        qr_out = qr.make_image(fill_color=self.qrcode_color)
        qr_out = qr_out.resize((self.qrcode_size, self.qrcode_size), Image.ANTIALIAS)
        height += self.qrcode_size

        return qr_out, height

    def gen_image(self, text: str, qrc: str = None, head_pic: BytesIO = None):
        img_font = ImageFont.truetype(self.font, self.font_size)

        text = self.__wrap(text)

        text_rows = len(text.split('\n'))

        width = self.width

        # 检查传入图片比例，计算和调整大小
        if head_pic:
            head, height = self.__resize_head(head_pic)
        else:
            head = None
            height = 0

        # 生成二维码
        if qrc:
            qr_out, height = self.__gen_qrcode(qrc, height)
        else:
            qr_out = None

        inner_height = (
                self.font_size * text_rows
                + (text_rows - 1) * self.line_space
        )
        height += 2 * (self.border_vertical_padding + self.text_vertical_padding) + inner_height

        out_img = Image.new(mode="RGB", size=(width, height), color=self.bg_color)
        draw = ImageDraw.Draw(out_img)

        # draw border
        x_padding = self.border_horizontal_padding
        top_padding = self.border_vertical_padding if not head else head.size[1] + self.border_vertical_padding
        bottom_padding = self.border_vertical_padding if not qr_out \
            else self.qrcode_size + self.border_vertical_padding
        draw.rectangle(((x_padding, top_padding), (width - x_padding, height - bottom_padding)),
                       fill=None, outline=self.border_color, width=4)

        # draw text
        text_x_padding = x_padding + self.text_horizontal_padding
        text_top_padding = top_padding + self.text_vertical_padding
        draw.text(
            (text_x_padding, text_top_padding), text, font=img_font, fill=self.font_color, spacing=self.line_space
        )

        # paste head
        if head:
            head_x_padding = int((width - head.size[0]) / 2)
            out_img.paste(head, (head_x_padding, 0))

        # paste qrcode
        if qr_out:
            qrcode_x_padding = int((width - self.qrcode_size) / 2)
            qrcode_y_padding = height - self.qrcode_size
            out_img.paste(qr_out, (qrcode_x_padding, qrcode_y_padding))

        return out_img

    def gen_bytes(self, text: str, qrc: str = None, head_pic: BytesIO = None) -> BytesIO:
        result = BytesIO()
        img = self.gen_image(text, qrc, head_pic)
        img.save(result, format="JPEG")

        return result

import logging

from mediawiki import MediaWiki

from urllib import parse

class Wiki:

    def __init__(self, api_url: str, fallback_url: str):
        self.api = MediaWiki(url=api_url)
        self.url = fallback_url

    async def get_from_api(self, title: str, is_template: bool):
        if is_template:
            title = "T:" + title
        result = self.api.opensearch(title, results=1)
        if result:
            title = result[0][0]
            url = result[0][2]
            result = f"标题：{title}\n链接：{url}"
        else:
            # result = self.url_parse(title)
            result = f"API未返回有效信息\n标题：{title}\n链接：{self.url + parse.quote(title)}"
        return result

    # async def url_parse(self, title: str):
    #     result = f"API未返回有效信息\n标题：{title}\n链接：{self.url + parse.quote(title)}"
    #     return result
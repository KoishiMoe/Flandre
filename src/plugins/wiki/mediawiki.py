# import requests
import aiohttp

'''
代码来自 pymediawiki 库（以MIT许可证开源），并根据bot的实际需要做了适量修改（主要是修改为静态方法以及减少不必要的api调用）
该库的Giuthub地址：https://github.com/barrust/mediawiki
许可证：https://github.com/barrust/mediawiki/blob/master/LICENSE
'''

USER_AGENT: str = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 ' + \
                  'Safari/537.36 '


class MediaWiki:

    @staticmethod
    async def test_api(api_url: str) -> bool:
        try:
            response = await MediaWiki._wiki_request(
                api_url, {"meta": "siteinfo", "siprop": "extensions|general"}
            )
        except:
            return False

        query = response.get("query", None)
        if query is None or query.get("general", None) is None:
            return False

        return True

    @staticmethod
    async def _wiki_request(api_url: str, params: dict) -> dict:
        params["format"] = "json"
        if "action" not in params:
            params["action"] = "query"

        return await MediaWiki._get_response(api_url, params)

    @staticmethod
    async def _get_response(api_url: str, params: dict):
        # session = requests.Session()
        # session.headers.update({"User-Agent": USER_AGENT})
        # return session.get(api_url, params=params, timeout=5000).json()
        headers = {"User-Agent": USER_AGENT}
        session = aiohttp.ClientSession()
        timeout = aiohttp.ClientTimeout(total=30)
        resp = await session.get(api_url, params=params, headers=headers, timeout=timeout)
        resp = await resp.json()
        await session.close()
        return resp

    @staticmethod
    async def _check_query(value, message):
        """ check if the query is 'valid' """
        if value is None or value.strip() == "":
            raise ValueError(message)

    @staticmethod
    async def opensearch(api_url: str, query: str, results: int = 10, redirect: bool = True) -> list:
        query_params = {
            "action": "opensearch",
            "search": query,
            "limit": (results if results is not None else 1),
            "redirects": ("resolve" if redirect else "return"),
            "warningsaserror": "True",
            "namespace": "",
        }

        results = await MediaWiki._wiki_request(api_url, query_params)

        await MediaWiki._check_error_response(results)

        res = []
        for i, item in enumerate(results[1]):
            res.append((item, results[2][i], results[3][i]))
        return res

    @staticmethod
    async def _check_error_response(response):
        """ check for default error messages and throw correct exception """
        if "error" in response:
            http_error = ["HTTP request timed out.", "Pool queue is full"]

            err = response["error"]["info"]
            if err in http_error:
                raise RuntimeError("HttpTimeoutError")
            raise RuntimeError(err)

    @staticmethod
    async def get_page_content(api_url: str, title: str) -> tuple:
        search_result = await MediaWiki.opensearch(api_url, title, results=1)  # 先找到真实title,防止有重定向导致内容为空
        if search_result:
            title = search_result[0][0]
        else:
            raise RuntimeError("未找到指定title")
        query_params: dict = {
            "prop": "extracts|revisions",
            "explaintext": "",
            "rvprop": "ids",
            "titles": title,
        }
        request = await MediaWiki._wiki_request(api_url, query_params)
        query = request["query"]
        pageid = list(query["pages"].keys())[0]
        page_info: dict = request["query"]["pages"][pageid]
        content = page_info.get("extract", None)

        if content is None:
            raise RuntimeError("Unable to extract page content")

        return content, search_result[0][2]

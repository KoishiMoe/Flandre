import requests

'''
代码来自 pymediawiki 库（以MIT许可证开源），并根据bot的实际需要做了适量修改（主要是修改为静态方法来减少不必要的api调用）
该库的Giuthub地址：https://github.com/barrust/mediawiki
许可证：https://github.com/barrust/mediawiki/blob/master/LICENSE
'''

USER_AGENT: str = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 ' + \
                  'Safari/537.36 '


class MediaWiki:

    @staticmethod
    def test_api(api_url: str) -> bool:
        try:
            response = MediaWiki._wiki_request(
                api_url, {"meta": "siteinfo", "siprop": "extensions|general"}
            )
        except:
            return False

        query = response.get("query", None)
        if query is None or query.get("general", None) is None:
            return False

        return True

    @staticmethod
    def _wiki_request(api_url: str, params: dict) -> dict:
        params["format"] = "json"
        if "action" not in params:
            params["action"] = "query"

        return MediaWiki._get_response(api_url, params)

    @staticmethod
    def _get_response(api_url: str, params: dict):
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        return session.get(api_url, params=params, timeout=5000).json()

    @staticmethod
    def _check_query(value, message):
        """ check if the query is 'valid' """
        if value is None or value.strip() == "":
            raise ValueError(message)

    @staticmethod
    def opensearch(api_url: str, query: str, results: int = 10, redirect: bool = True) -> list:
        query_params = {
            "action": "opensearch",
            "search": query,
            "limit": (results if results is not None else 1),
            "redirects": ("resolve" if redirect else "return"),
            "warningsaserror": True,
            "namespace": "",
        }

        results = MediaWiki._wiki_request(api_url, query_params)

        MediaWiki._check_error_response(results, query)

        res = list()
        for i, item in enumerate(results[1]):
            res.append((item, results[2][i], results[3][i]))
        return res

    @staticmethod
    def _check_error_response(response, query):
        """ check for default error messages and throw correct exception """
        if "error" in response:
            http_error = ["HTTP request timed out.", "Pool queue is full"]

            err = response["error"]["info"]
            if err in http_error:
                raise RuntimeError("HttpTimeoutError")
            raise RuntimeError(err)

    @staticmethod
    def get_page_content(api_url: str, title: str) -> str:
        query_params: dict = {
            "prop": "extracts|revisions",
            "explaintext": "",
            "rvprop": "ids",
            "titles": title,
        }
        request = MediaWiki._wiki_request(api_url, query_params)
        query = request["query"]
        pageid = list(query["pages"].keys())[0]
        page_info: dict = request["query"]["pages"][pageid]
        content = page_info.get("extract", None)

        if content is None:
            raise RuntimeError("Unable to extract page content")

        return content

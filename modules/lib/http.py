import requests

from ..debug import debug

class WebClient(requests.Session):
    def __init__(self, base_url=None):
        super().__init__()
        self.base_url = base_url

    def request(self, method, url, *args, **kwargs):
        if self.base_url:
            url = self.base_url + url
        resp = super().request(method, url, *args, **kwargs)
        if not resp.ok:
            raise HttpError(resp)
        debug(
            "Request is OK! ({} {})", 
            resp.request.method,
            resp.request.url.split("?")[0]
        )
        return resp

class HttpError(Exception):
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return (
            f"Ошибка при запросе к {self.response.request.url!r}:"
            f"\n{self.response.text}"
        )

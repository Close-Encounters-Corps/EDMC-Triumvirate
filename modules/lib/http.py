import requests


class WebClient(requests.Session):
    def __init__(self, base_url=None):
        super().__init__()
        self.base_url = base_url

    def request(self, method, url, *args, **kwargs):
        if self.base_url:
            url = self.base_url + url
        resp = super().request(method, url, *args, **kwargs)
        return resp


class HttpError(Exception):
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return (
            f"Ошибка при запросе к {self.response.request.url!r}:"
            f"\n{self.response.text}"
        )

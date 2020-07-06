import requests

import settings

from .thread import BasicThread
from ..debug import debug, error

class CecApi(requests.Session):
    def __init__(self, url, token):
        super().__init__()
        self.base_url = url
        self.token = token

    def request(self, method, url, **kwargs):
        headers = kwargs.get("headers")
        if headers is not None:
            del kwargs["headers"]
        else:
            headers = {}
        headers["Token"] = self.token
        url = self.base_url + "/api/triumvirate" + url

        resp = super().request(method, url, **kwargs)
        return resp

    def sumbit(self, url, json):
        thread = BasicThread(target=lambda: self.post(url, json=json))
        thread.start()
        return thread

    def do_submit(self, url, json):
        try:
            self.post(url, json=json)
        except ApiError as e:
            error(f"Error on submitting data: {e}")



class ApiError(Exception):
    pass

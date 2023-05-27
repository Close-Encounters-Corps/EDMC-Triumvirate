from .http import WebClient
from .thread import BasicThread
from .utils import get_endpoint
from settings import canonn_realtime_url


class CanonnApi(WebClient):
    def __init__(self, is_beta=False):
        endpoint = get_endpoint(is_beta=is_beta)
        super().__init__(base_url=endpoint)


class CanonnRealtimeApi(WebClient):
    def __init__(self):
        super().__init__(base_url=canonn_realtime_url)

    def sumbit_game_version(self, entry):
        job = BasicThread(target=lambda: self._submit_game_version(entry))
        job.start()
        return job

    def _submit_game_version(self, entry):
        self.post("/postGameVersion", json=entry)

    def submit_client(self, payload):
        job = BasicThread(target=lambda: self._submit_client(payload))
        job.start()
        return job

    def _submit_client(self, payload):
        self.post("/submitClient", payload)

from ..debug import debug
from .context import global_context
from .http import WebClient
from .thread import BasicThread
from ..release import Environment, Release
import settings

def get_endpoint(is_beta=False):
    urls = {
        Environment.LIVE: settings.canonn_live_url,
        Environment.STAGING: settings.canonn_staging_url,
        Environment.DEVELOPMENT: settings.canonn_dev_url,
    }
    if is_beta:
        return urls[Environment.STAGING]
    env = env = global_context.by_class(Release).env
    return urls[env]

class CanonnApi(WebClient):
    def __init__(self, is_beta=False):
        endpoint = get_endpoint(is_beta=is_beta)
        super().__init__(base_url=endpoint)


class CanonnRealtimeApi(WebClient):
    def __init__(self):
        super().__init__(base_url=settings.canonn_realtime_url)

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

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

    def submit_materialreward(self, entry):
        categories = {
            "$MICRORESOURCE_CATEGORY_Manufactured;": "Manufactured",
            "$MICRORESOURCE_CATEGORY_Encoded;": "Encoded",
            "$MICRORESOURCE_CATEGORY_Raw;": "Raw",
        }
        reward = entry.data["MaterialsReward"][0]
        category = categories[reward["Category"]]

        payload = dict(
            system=entry.system,
            distancefromMainStar=entry.dist_from_star,
            coordX=entry.coords.x,
            coordY=entry.coords.y,
            coordZ=entry.coords.z,
            isBeta=entry.is_beta,
            clientVersion=entry.client,
            factionState=entry.sys_faction.state,
            factionAllegiance=entry.sys_faction.allegiance,
            body=entry.body,
            latitude=entry.lat,
            longitude=entry.lon,
            # additional fields
            collectedFrom="missionReward",
            journalName=reward["Name"],
            count=reward["Count"],
            category=category,
        )
        return self.post("/materialreports", json=payload)

    def submit_materialscollected(self, entry):
        collected_from = "scanned" if entry.data["Category"] == "Encoded" else "collected"
        payload = dict(
            system=entry.system,
            distancefromMainStar=entry.dist_from_star,
            coordX=entry.coords.x,
            coordY=entry.coords.y,
            coordZ=entry.coords.z,
            isBeta=entry.is_beta,
            clientVersion=entry.client,
            factionState=entry.sys_faction.state,
            factionAllegiance=entry.sys_faction.allegiance,
            body=entry.body,
            latitude=entry.lat,
            longitude=entry.lon,
            # additional fields
            collectedFrom=collected_from,
            category = entry.data["Category"],
            journalName = entry.data["Name"],
            count = entry.data["Count"]
        )
        # from pprint import pprint
        # pprint(payload)
        return self.post("/materialreports", json=payload)


class CanonnRealtimeApi(WebClient):
    def __init__(self):
        super().__init__(base_url=settings.canonn_realtime_url)

    # def submit_nhss(self, entry, threat_level):
    #     params = dict(
    #         cmdrName=entry.cmdr,
    #         systemName=entry.system,
    #         x=entry.coords.x,
    #         y=entry.coords.y,
    #         z=entry.coords.z,
    #         threat_level=threat_level
    #     )
    #     return self.get("/submitNHSS", params=params)

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

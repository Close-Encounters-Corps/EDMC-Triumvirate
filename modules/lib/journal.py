
class Faction:
    def __init__(self, state, allegiance):
        self.state = state
        self.allegiance = allegiance

class Coords:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

class JournalEntry:
    def __init__(
        self,
        cmdr:       str,
        is_beta:    bool,
        system:     str,
        systemAddress:      int,
        sys_faction_state:  str,
        sys_faction_allegiance: str,
        dist_from_star:     float,
        station:    str,
        data:       dict,
        state:      dict,
        x:          float,
        y:          float,
        z:          float,
        body:       str,
        lat:        float,
        lon:        float,
        client:     str,
    ):
        self.cmdr = cmdr
        self.is_beta = is_beta
        self.system = system
        self.systemAddress = systemAddress
        self.sys_faction = Faction(state=sys_faction_state, allegiance=sys_faction_allegiance)
        self.dist_from_star = dist_from_star
        self.station = station
        self.data = data
        self.state = state
        self.coords = Coords(x, y, z)
        self.body = body
        self.lat = lat
        self.lon = lon
        self.client = client

    def as_dict(self):
        return {
            "cmdr": self.cmdr,
            "is_beta": self.is_beta,
            "system": self.system,
            "systemAddress": self.systemAddress,
            "station": self.station,
            "system_faction": {
                "state": self.sys_faction.state,
                "allegiance": self.sys_faction.allegiance
            },
            "data": self.data,
            "body": self.body,
            "state": self.state,
            "dist_from_star": self.dist_from_star,
            "coords": {
                "x": self.coords.x,
                "y": self.coords.y,
                "z": self.coords.z,
                "lat": self.lat,
                "lon": self.lon
            },
            "client": self.client
        }
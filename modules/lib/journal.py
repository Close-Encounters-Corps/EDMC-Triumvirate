
class Faction:
    def __init__(self, state, allegiance):
        self.state = state
        self.allegiance = allegiance

class Coords:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class JournalEntry:
    def __init__(
        self,
        cmdr,
        is_beta,
        system,
        sys_faction_state,
        sys_faction_allegiance,
        dist_from_star,
        station,
        data,
        state,
        x,
        y,
        z,
        body,
        lat,
        lon,
        client,
    ):
        self.cmdr = cmdr
        self.is_beta = is_beta
        self.system = system
        self.sys_faction = Faction(state=sys_faction_state, allegiance=sys_faction_allegiance)
        self.dist_from_star = dist_from_star
        self.station = station
        self.data = data
        self.state = state
        self.coords = Coords(x, y, z)
        self.body = body
        self.lat = lat
        self.lon = lon

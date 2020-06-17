import requests

from settings import edsm_poi_url

from .patrol import build_patrol
from ..lib.context import global_context

types = {
    "minorPOI": "Minor Point of Interest",
    "planetaryNebula": "Planetary Nebula",
    "nebula": "Nebula",
    "blackHole": "Black Hole",
    "historicalLocation": "Historical Location",
    "stellarRemnant": "Stellar Remnant",
    "planetFeatures": "Planet Features",
    "regional": "Regional",
    "pulsar": "Pulsar",
    "starCluster": "Star Cluster",
    "jumponiumRichSystem": "Jumponium Rich System",
    "surfacePOI": "Surface Point of Interest",
    "deepSpaceOutpost": "Deep Space Outpost",
    "mysteryPOI": "Mystery Point of Interest",
    "organicPOI": "Organic Point of Interest",
    "restrictedSectors": "Restricted Sector",
    "geyserPOI": "Geyser Point of Interest",
    "region": "Region",
    "travelRoute": "Travel Route",
    "historicalRoute": "Historical Route",
    "minorRoute": "Minor Route",
    "neutronRoute": "Neutron Route",
}

validtypes = [
    "minorPOI",
    "planetaryNebula",
    "nebula",
    "blackHole",
    "historicalLocation",
    "stellarRemnant",
    "planetFeatures",
    "regional",
    "pulsar",
    "starCluster",
    "jumponiumRichSystem",
    "surfacePOI",
    "deepSpaceOutpost",
    "mysteryPOI",
    "organicPOI",
    "restrictedSectors",
    "geyserPOI",
]


def get_edsm_patrol() -> list:
    from .patrol_module import PatrolModule
    patrol = global_context.by_class(PatrolModule)

    r = requests.get(edsm_poi_url)
    r.encoding = "utf-8"
    entries = r.json()

    edsm_patrol = []

    patrol.patrol_name = "Galactic Mapping"

    for entry in entries:

        if entry.get("type") in validtypes and "Archived: " not in entry.get("name"):
            coords = (
                float(entry.get("coordinates")[0]),
                float(entry.get("coordinates")[1]),
                float(entry.get("coordinates")[2]),
            )
            instructions = "Galactic Mapping Project: {} : {}".format(
                types.get(entry.get("type")), entry.get("name"),
            )
            item = build_patrol(
                type="Galactic Mapping",
                system=entry.get("galMapSearch"),
                coords=coords,
                instructions=instructions,
                url=entry.get("galMapUrl")
            )
            edsm_patrol.append(item)

    patrol.event_generate("<<PatrolDone>>", when="tail")
    return edsm_patrol



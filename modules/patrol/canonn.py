from contextlib import closing
import csv

import requests

from settings import canonn_patrols_url

from ..lib.spreadsheet import Spreadsheet
from ..debug import debug, error
from .patrol import build_patrol

class CanonnPatrols(list):

    @classmethod
    def new(cls):
        output = cls()
        spreadsheet = Spreadsheet(canonn_patrols_url)
        for row in spreadsheet:
            id_, enabled, description, type_, link = row
            if enabled == "Y":
                if type_ == "json":
                    debug("{} Patrol enabled".format(description))
                    output += cls.from_json(link)
                elif type_ == "tsv":
                    debug("{} Patrol enabled".format(description))
                    output += cls.from_tsv(link)
                else:
                    debug("no patrol {}".format(row))
            else:
                debug("{} Patrol disabled".format(description))
        return output


    @classmethod
    def from_json(cls, url):
        patrols = []
        resp = requests.get(url).json()
        for row in resp:
            patrol = build_patrol(
                type=row.get("type"),
                system=row.get("system"),
                coords=[float(x) for x in (row.get("x"), row.get("y"), row.get("z"))],
                instructions=row.get("instructions"),
                url=row.get("url"),
                event=row.get("event")
            )
            patrols.append(patrol)
        return cls(patrols)

    # deprecated?
    @classmethod
    def from_tsv(cls, url):
        patrols = []
        with closing(requests.get(url, stream=True)) as resp:
            reader = csv.reader(resp.raw, delimiter="\t")
            next(reader)
            for row in reader:
                patrol = build_patrol(
                    type=row[0],
                    system=row[1],
                    coords=[float(x) for x in (row[2], row[3], row[4])],
                    instructions=row[5],
                    url=row[6],
                    event=row[7]
                )
                if not patrol["system"]:
                    error(f"No system in patrol {patrol}")
                    continue
                patrols.append(patrol)
        return cls(patrols)

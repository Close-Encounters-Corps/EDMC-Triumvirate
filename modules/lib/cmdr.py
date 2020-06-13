# -*- coding: utf-8 -*-
import csv
from contextlib import closing

import requests

import settings

def find_cmdr(name):
    with closing(requests.get(settings.users_base_url, stream=True)) as r:
        # try/except для целей совместимости py2/py3
        if settings.PY3:
            from modules.lib.py3utils import BytesDecoder
            stream = BytesDecoder(r.raw) # pylint:disable=no-member
        else:
            stream = r.raw # pylint:disable=no-member
        reader = csv.reader(stream, delimiter="\t")
        # пропускаем заголовок
        next(reader)

        for row in reader:
            cmdr, squadron, SQID = row
            if cmdr == name:
                return Commander(name, squadron, SQID)

class Commander(object):
    def __init__(self, name, squadron, sqid):
        self.name = name
        self.squadron = squadron
        self.sqid = sqid

# -*- coding: utf-8 -*-
import csv
from contextlib import closing

import requests

import settings

from modules.debug import debug

class IteratorLogger(object):
    def __init__(self, obj):
        self.obj = obj

    def __iter__(self):
        for line in self.obj:
            debug("Processing line ({}) {}", type(line), line)
            yield line
        

def find_cmdr(name):
    debug("Looking for commander {}".format(name))
    with closing(requests.get(settings.users_base_url, stream=True)) as r:
        if settings.PY3:
            from modules.lib.py3utils import BytesDecoder
            stream = BytesDecoder(r.raw) # pylint:disable=no-member
        else:
            stream = r.raw # pylint:disable=no-member
        stream = IteratorLogger(stream)
        reader = csv.reader(stream, delimiter="\t")
        # пропускаем заголовок
        next(reader)

        for row in reader:
            cmdr, squadron, SQID = row
            if cmdr == name:
                debug("Found commander: {}".format(cmdr))
                return Commander(name, squadron, SQID)

class Commander(object):
    def __init__(self, name, squadron, sqid):
        self.name = name
        self.squadron = squadron
        self.sqid = sqid

    def __str__(self):
        return "{}({}, squadron={}, sqid={})".format(
            self.__class__.__name__,
            self.name,
            self.squadron,
            self.sqid
        )
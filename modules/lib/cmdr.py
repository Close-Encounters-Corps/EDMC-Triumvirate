# -*- coding: utf-8 -*-
import csv

import requests

import settings

from modules.debug import debug


class IterWrapper(object):
    def __init__(self, obj):
        self.obj = obj

    def __iter__(self):
        for line in self.obj:
            # debug("Processing line '{}'", line)
            yield line.decode()


def find_cmdr(name):
    name = str(name)
    debug("Looking for commander {}", name)
    # TODO после перехода на py3 попробовать переписать
    # запрос на requests.get(..., stream=True)
    resp = requests.get(settings.users_base_url)
    stream = IterWrapper(resp.content.splitlines())
    reader = csv.reader(stream, delimiter="\t")
    try:
        # пропускаем заголовок
        next(reader)
        for row in reader:
            cmdr, squadron, SQID = row
            # debug("Comparing: {} ({})", cmdr, type(cmdr))
            if cmdr == name:
                cmdrobj = Commander(name, squadron, SQID)
                debug("Commander found! ({})", cmdrobj)
                return cmdrobj
    except csv.Error:
        debug("Error at reading CSV (line {}):", reader.line_num)
        raise


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

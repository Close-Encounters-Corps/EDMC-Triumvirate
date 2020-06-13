# -*- coding: utf-8 -*-

class Context(object):
    """
    Хранилище состояния плагина.
    Текущий командир, его координаты, и прочее.
    """
    def __init__(self):
        # хак чтобы обойти вызов setattr'а и таким образом избежать рекурсии
        self.__dict__["_store"] = {}

    def __getattr__(self, name):
        try:
            return self._store[name]
        except KeyError:
            raise AttributeError(name) # TODO дописать 'from None' после py3

    def __setattr__(self, name, value):
        self._store[name] = value

    def dump(self):
        from modules.debug import debug
        debug(self._store)

global_context = Context()

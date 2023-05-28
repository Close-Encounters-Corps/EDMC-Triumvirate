import typing as ty

from .module import Module

class Context(object):
    """
    Хранилище состояния плагина.
    Текущий командир, его координаты, и прочее.
    """
    def __init__(self):
        # хак чтобы обойти вызов setattr'а и таким образом избежать рекурсии
        self.__dict__["_store"] = {}
        self.modules: ty.List[Module] = []

    def __getattr__(self, name):
        try:
            return self._store[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self._store[name] = value

    def by_class(self, cls):
        for x in self.modules:
            if isinstance(x, cls):
                return x
        raise KeyError(cls)

    @property
    def enabled_modules(self):
        return [mod for mod in self.modules if mod.enabled]

    def dump(self):
        from modules.debug import debug
        debug(self._store)

global_context = Context()

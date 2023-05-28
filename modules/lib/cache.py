from .thread import Thread
from ..debug import debug

class Cache(Thread):
    def __init__(self, max_size: int, static: dict=None):
        super().__init__(name="CACHE")
        self.max_size = max_size
        self.static = static or {}
        self.items = {}
        self._key_order = []

    def __getitem__(self, item):
        val = self.static.get(item)
        if val is None:
            val = self.items.get(item)
        if not val:
            raise KeyError(item)
        return val

    def __setitem__(self, key, value):
        self.items[key] = value
        self._key_order.append(key)

    def do_run(self):
        while 1:
            self._do_check()
            self.sleep(10)

    def _do_check(self):
        size_to_remove = len(self.items) - self.max_size 
        if size_to_remove >= 0:
            for i in range(size_to_remove or 1):
                key = self._key_order.pop(i)
                debug("[Cache] Removing key {}", key)
                del self.items[key]

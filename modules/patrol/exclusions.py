import os.path

import json

from context import PluginContext

class PatrolExclusions(dict):
    def __init__(self, path, **kwargs):
        super().__init__(BGS={}, SHIPS={})
        self.path = path

    @classmethod
    def from_file(cls):
        pth = os.path.join(PluginContext.plugin_dir, "userdata", "EDMC-Triumvirate.patrol")
        out = cls(pth)
        out.load()
        return out

    def load(self) -> dict:
        if not os.path.exists(self.path):
            return
        with open(self.path) as fd:
            self.update(json.load(fd))

    def save(self, data):
        for patrol in data:
            patrol_type = patrol["type"]
            if patrol_type not in self.keys():
                continue
            if patrol.get("excluded"):
                self[patrol_type][patrol["system"]] = True
        with open(self.path, "w") as fd:
            json.dump(self, fd)

import json
import re

from modules.debug import debug
from modules.lib.module import Module
from modules.lib.conf import config as plugin_config

from ._dataitem import _DataItem
from .ui import VisualizerView, VSettingsFrame


class VisualizerModel:
    PLUGIN_CONFIG_KEY   = "Visualizer.config"
    DEFAULT_CATEGORY    = "None"

    def __init__(self, view_instance: VisualizerView):
        self.view = view_instance
        self.registered_modules: list[Module] = list()

        self.__saved_config = self._load_config()       # это меняется ТОЛЬКО в _save_config()
        self.visualizer_shown: bool = self.__saved_config["visualizer_shown"]
        self.view.change_visibility(self.visualizer_shown)
        self.modules_display_status: dict[str, bool] = self.__saved_config["modules_display_status"].copy()    # чтобы __saved_config не менялся

        self.current_system: str | None = None
        self.data: list[_DataItem] = list()


    def add_module(self, module: Module):
        self.registered_modules.append(module)
        qualname = module.__class__.__qualname__
        if not qualname in self.modules_display_status:
            self.modules_display_status[qualname] = True
            self._save_config()
        debug("[Visualizer] Module {} registered, display status: {}.", qualname, self.modules_display_status[qualname])


    def add_data(self, module: Module, category: str, body: str, text: str):
        assert module in self.registered_modules, "Module must be registered first. Refer to Visualizer.register()"

        debug("[Visualizer] Got new data from {}: category '{}', body '{}', text '{}'.", module, category, body, text)
        if category == None:
            category = self.DEFAULT_CATEGORY
            debug("[Visualizer] Category was None, setting to default ('{}').", category)
        data_item = _DataItem(module, category, body, text)
        self.data.append(data_item)
        if self.modules_display_status[data_item.m_qualname] == True:
            self.view.display(data_item)


    def is_data_shown_from(self, module: Module):
        assert module in self.registered_modules, "Module must be registered first. Refer to Visualizer.register()"
        qualname = module.__class__.__qualname__
        return self.modules_display_status[qualname]


    def update_system(self, system: str | None):
        debug("[Visualizer] Detected system change, clearing data.")
        if self.current_system != system:
            self.clear()
            self.current_system = system


    def get_settings_frame(self, parent, row):
        shown = self.visualizer_shown
        config: list[tuple[str, str, bool]] = list()    # (Module.__qualname__, Module.localized_name, статус)
        for mod in self.registered_modules:
            qualname = mod.__class__.__qualname__
            name = mod.localized_name
            enabled = self.modules_display_status[qualname]
            config.append( (qualname, name, enabled) )
        self.__settings_frame = VSettingsFrame(parent, row, shown, config)
        return self.__settings_frame
    

    def update_user_settings(self):
        shown, config = self.__settings_frame.get_current_config()
        self.visualizer_shown = shown
        self.modules_display_status = config
        self._save_config()

        self.view.clear()
        data_for_display = [item for item in self.data  if self.modules_display_status[item.m_qualname] == True]
        if len(data_for_display) > 0:
            self.view.display(data_for_display)

        self.view.change_visibility(self.visualizer_shown)


    def clear(self):
        self.data.clear()
        self.view.clear()


    def _load_config(self) -> dict:
        config = plugin_config.get_str(self.PLUGIN_CONFIG_KEY)
        if not config:
            config = {
                "visualizer_shown": True,
                "modules_display_status": {}
            }
            debug("[Visualizer] No saved config found, setting to default.")
        else:
            debug("[Visualizer] Loaded config: {}", config)
            config = json.loads(config)

        return config


    def _save_config(self):
        config = {
            "visualizer_shown":         self.visualizer_shown,
            "modules_display_status":   self.modules_display_status
        }
        plugin_config.set(self.PLUGIN_CONFIG_KEY, json.dumps(config))
        self.__saved_config = config
        debug("[Visualizer] Config saved: {}", config)
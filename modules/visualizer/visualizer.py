import json

from modules.lib.journal import JournalEntry
from ._internal import _VisualizerFrame, _VisualizerSettingsFrame, _DataItem, CATEGORIES

from modules.lib.module import Module
from modules.lib.conf import config as plugin_config
from modules.debug import debug

# для аннотаций типов
import tkinter as tk



class Vizualizer(Module):
    """
    Модуль для объединённого вывода информации по текущей системе
    из других модулей с разбивкой инфы по категориям.
    Духовный наследник старого модуля Кодекса в контексте отображения.
    """

    def __init__(self, parent: tk.Misc, row: int):
        super().__init__()
        self.parent = parent
        self.row = row
        self.current_system = None

        self.shown = plugin_config.get_bool("Visualizer.shown")
        if self.shown is None:
            self.shown = True
            plugin_config.set("Visualizer.shown", True)
        
        self.__config = self.__get_saved_config()
        self.__registered_modules: list[Module] = []
        self.__frame = None

    
    def on_start(self, plugin_dir: str):
        self.plugin_dir = plugin_config
        self.__frame = _VisualizerFrame(self.parent, self.row, self.shown, plugin_dir, self.__config)


    def register(self, module: Module):
        """Добавление модуля в список визуализатора."""
        module_name = module.__class__.__qualname__
        state = self.__config.get(module_name)
        if state is None:
            self.__config[module_name] = True
            self.__save_config()
        self.__registered_modules.append(module)


    def visualize(self, caller: Module, category: str, body: str, string: str, no_shrink: bool = False):
        """
        Передача информации о POI для отображения в визуализаторе.

        *caller* - модуль, вызывающий метод. Просто передавайте self.

        *category* - одно из CATEGORIES, в противном случае назначается категория по-умолчанию (None).

        *body* - тело. При передаче полного названия часть с именем системы отбрасывается ('Sector AA-A h0 A 1 a' -> 'A 1 a').

        *string* - собственно информация по POI. Выводится как дано, локализация при необходимости должна быть проведена ранее.

        *no_shrink* - отключает сокращение названия тела (*body*). Не рекомендуется к использованию - окно EDMC не резиновое.
        """
        if not self.__frame:
            raise RuntimeError("Visualizer is not ready yet, wait for the plugin to load completely.")
        if not caller in self.__registered_modules:
            raise ValueError(f'Module {caller.__class__.__qualname__} is not registered. Use Visualizer.register()')
        self.__frame.add_data(_DataItem(caller, category, body, string, no_shrink))


    def is_module_enabled(self, module: Module) -> bool:
        """Сообщает, включено ли пользователем отображение информации из модуля."""
        module_name = module.__class__.__qualname__
        registered = module in self.__registered_modules
        if not registered:
            raise ValueError(f'Module {module_name} is not registered. Use Visualizer.register()')
        return self.__config[module_name]


    def get_registered_modules(self) -> list[Module]:
        return self.__registered_modules.copy()


    def get_enabled_modules(self) -> list[Module]:
        return [module for module in self.__registered_modules if self.__config[module.__class__.__qualname__] == True]
    

    def draw_settings(self, parent_widget: tk.Misc, cmdr: str, is_beta: bool, row: int):
        self.__settings_frame = _VisualizerSettingsFrame(self, parent_widget, row)
        return self.__settings_frame
    

    def on_settings_changed(self, cmdr: str, is_beta: bool):
        self.shown, self.__config = self.__settings_frame.get_current_config()
        self.__frame.is_shown = self.shown
        self.__frame.update_config(self.__config)

        debug("[Visualizer.on_settings_changed] Got new config: {}", self.__config)
        self.__save_config()
        
        del self.__settings_frame

    
    def on_journal_entry(self, entry: JournalEntry):
        if entry.system != self.current_system:
            self.__frame.clear()
    

    def __get_saved_config(self) -> dict[str, bool]:
        """
        Возвращаемый конфиг: key = type[Module].__qualname__, val: bool
        """
        config = {}
        string = plugin_config.get_str("Visualizer.modulesSettings")
        if string:
            config = json.loads(string)
        return config
    

    def __save_config(self):
        plugin_config.set("Visualizer.shown", self.shown)
        plugin_config.set("Visualizer.modulesSettings", json.dumps(self.__config))
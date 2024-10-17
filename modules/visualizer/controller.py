import tkinter as tk

from settings import poi_categories as CATEGORIES
from .ui import VisualizerView
from .model import VisualizerModel
from modules.lib.journal import JournalEntry
from modules.lib.module import Module


class VisualizerController(Module):
    """
    Модуль для объединённого вывода информации по текущей системе
    из других модулей с разбивкой инфы по категориям.
    Духовный наследник старого модуля Кодекса в контексте отображения.
    """

    def __init__(self, parent: tk.Misc, row: int):
        super().__init__()
        self.__view = VisualizerView(parent, row)
        self.__model = VisualizerModel(self.__view)


    # а-ля публичный интерфейс: методы для вызова из других модулей

    def register(self, module: Module) -> None:
        """
        Добавляет модуль в список к отображению.
        Обязательно к использованию ДО вызова Visualizer.show(),
        в идеале во время инициализации модуля.

        module : Module
            Просто передайте self
        """
        assert isinstance(module, Module)
        self.__model.add_module(module)
    

    def show(self, caller: Module, body: str, text: str, category: str = None) -> None:
        """
        Добавляет запись в список данных к отображению.

        caller : Module
            Просто передайте self
        body : str
            Тело, к которому относится запись
        text : str
            Текст записи; при необходимости перевода - эта часть на вашей совести
        category : str, optional
            Категория записи; при отсутствии будет назначена категорию по-умолчанию
        """
        assert isinstance(caller, Module)
        assert isinstance(body, str)
        assert isinstance(text, str)
        assert category in CATEGORIES or category is None
        self.__model.add_data(caller, category, body, text)


    def is_display_enabled_for(self, module: Module) -> bool:
        assert isinstance(module, Module)
        return self.__model.is_data_shown_from(module)
    

    # методы, специфичные для Module

    def on_journal_entry(self, entry: JournalEntry):
        self.__model.update_system(entry.system)
    
    def draw_settings(self, parent_widget: tk.Misc, cmdr: str, is_beta: bool, row: int):
        return self.__model.get_settings_frame(parent_widget, row)

    def on_settings_changed(self, cmdr: str, is_beta: bool):
        self.__model.update_user_settings()
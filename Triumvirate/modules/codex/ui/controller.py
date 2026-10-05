import tkinter as tk

from Triumvirate.core.settings import poi_categories as CATEGORIES
from Triumvirate.core.shortcuts import _translate
from Triumvirate.lib.journal import JournalEntry
from Triumvirate.lib.module import Module

from .model import CodexUIModel
from .view import CodexUIView


class CodexUIController(Module):
    """
    Модуль для объединённого вывода информации по текущей системе
    из исследовательских модулей с разбивкой инфы по категориям.
    Духовный наследник старого модуля Кодекса в контексте отображения.
    """

    @property
    def localized_name(self) -> str:
        return _translate("Visualizer")


    def __init__(self, parent: tk.Misc, row: int):
        super().__init__()
        self.__view = CodexUIView(parent, row)
        self.__model = CodexUIModel(self.__view)


    # а-ля публичный интерфейс: методы для вызова из других модулей

    def register(self, module_instance: Module) -> None:         # noqa: E301
        """
        Добавляет модуль в список к отображению.
        Обязательно к использованию ДО вызова Visualizer.show(),
        в идеале во время инициализации модуля.

        module : Module
            Просто передайте self
        """
        assert isinstance(module_instance, Module)
        self.__model.add_module(module_instance)


    def show(self, caller: Module, text: str, category: str | None = None, location: str | None = None) -> None:
        """
        Добавляет запись в список данных к отображению.

        caller : Module
            Просто передайте self
        text : str
            Текст записи; при необходимости перевода - эта часть на вашей совести
        category : str, optional
            Категория записи; при отсутствии будет назначена категорию по-умолчанию
        location : str, optional
            Местоположение POI
        """
        assert isinstance(caller, Module)
        assert isinstance(text, str)
        assert category in CATEGORIES or category is None
        self.__model.add_data(caller, category, location, text)


    def display_enabled_for(self, module: Module) -> bool:
        assert isinstance(module, Module)
        return self.__model.is_data_shown_from(module)


    # методы, специфичные для Module

    def on_journal_entry(self, entry: JournalEntry):  # noqa: E301
        self.__model.update_system(entry.system)

    def draw_settings(self, parent_widget: tk.Misc, cmdr: str, is_beta: bool, row: int):
        self.__model.draw_settings_frame(parent_widget, row)

    def on_settings_changed(self, cmdr: str, is_beta: bool):
        self.__model.update_user_settings()

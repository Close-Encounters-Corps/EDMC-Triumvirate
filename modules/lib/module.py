from abc import ABC, ABCMeta
from l10n import translations as tr

# для аннотаций типов:
import tkinter as tk
from modules.lib.journal import JournalEntry
from typing import Type, TypeVar


class ModuleMeta(ABCMeta):
    _instances = dict()    
    def __call__(cls, *args, **kwargs):
        """
        Модификация конструктора модулей.
        Реализует синглтон для каждого из наследников Module.
        """
        if not cls._instances.get(cls):
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Module(ABC, metaclass=ModuleMeta):
    """
    Интерфейс, описывающий модуль и доступные ему "хуки".
    """

    def on_start(self, plugin_dir: str):
        """
        Вызывается при старте плагина.
        """

    def draw_settings(self, parent_widget: tk.Misc, cmdr: str, is_beta: bool, row: int):
        """
        Вызывается при отрисовки окна настроек.
        """

    def on_settings_changed(self, cmdr: str, is_beta: bool):
        """
        Вызывается в момент, когда пользователь
        сохраняет настройки.
        """

    def on_journal_entry(self, entry: JournalEntry):
        """
        Вызывается при появлении новой записи в логах.
        """

    def on_cmdr_data(self, data: dict, is_beta: bool):
        """
        Вызывается при появлении новых данных о командире.
        """

    def on_dashboard_entry(self, cmdr: str, is_beta: bool, entry: dict):
        """
        Вызывается при обновлении игрой status.json
        """

    def on_chat_message(self, entry: JournalEntry):
        """
        Вызывается при появлении новой записи типа сообщения в логах.
        """

    def close(self):
        """
        Вызывается в момент завершения работы плагина.
        """

    @property
    def enabled(self) -> bool:
        """
        Сообщает, включен ли плагин.
        """
        return True
    
    @property
    def localized_name(self) -> str:
        """
        Возвращает имя модуля в выбранной локализации. Ключ для строк перевода - __qualname__
        """
        return tr.tl(self.__class__.__qualname__)


T = TypeVar('T', bound=Module)
def get_module_instance(module_class: Type[T]) -> T | None:
    return ModuleMeta._instances.get(module_class)


def get_active_modules():
    return [instance for instance in ModuleMeta._instances.values() if instance.enabled]


def list_active_modules_names():
    return [instance.__class__.__name__ for instance in ModuleMeta._instances.values() if instance.enabled]
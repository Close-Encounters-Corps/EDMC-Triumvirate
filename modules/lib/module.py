from abc import ABC, ABCMeta, abstractmethod
from typing import Type, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    # для аннотаций типов
    import tkinter as tk
    from modules.lib.journal import JournalEntry


class ModuleMeta(ABCMeta):
    _instances = dict()

    def __new__(cls, name, bases, dct):
        """
        Модификация определения модулей.
        Задаёт дефолтные значения полям `enabled` и `localized_name`,
        если они отсутствуют в определении класса.
        """
        if "enabled" not in dct:
            dct["enabled"] = True
        if "localized_name" not in dct:
            dct["localized_name"] = name
        return super().__new__(cls, name, bases, dct)

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

    def draw_settings(self, parent_widget: 'tk.Misc', cmdr: str, is_beta: bool, row: int) -> 'tk.Misc':
        """
        Вызывается при отрисовки окна настроек.
        """

    def on_settings_changed(self, cmdr: str, is_beta: bool):
        """
        Вызывается в момент, когда пользователь
        сохраняет настройки.
        """

    def on_journal_entry(self, entry: 'JournalEntry'):
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

    def on_chat_message(self, entry: 'JournalEntry'):
        """
        Вызывается при появлении новой записи типа сообщения в логах.
        """

    def on_close(self):
        """
        Вызывается в момент завершения работы плагина.
        """

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """
        Сообщает, включен ли модуль.
        """

    @property
    @abstractmethod
    def localized_name(self) -> str:
        """
        Возвращает имя модуля в выбранной локализации. По-умолчанию отдаёт имя класса.
        Реализацией предполагается _translate() и читабельные названия в строках перевода для отображения в GUI.
        """


T = TypeVar('T', bound=Module)
def get_module_instance(module_class: Type[T]) -> T | None:     # noqa: E302
    return ModuleMeta._instances.get(module_class)


def get_active_modules() -> list[Module]:
    return [instance for instance in ModuleMeta._instances.values() if instance.enabled]


def list_active_modules_names() -> list[str]:
    return [instance.__class__.__name__ for instance in ModuleMeta._instances.values() if instance.enabled]

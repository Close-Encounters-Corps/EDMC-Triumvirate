from abc import ABC, abstractmethod

class Module(ABC):
    """
    Интерфейс, описывающий модуль и доступные ему "хуки".
    """

    @abstractmethod
    def on_start(self, plugin_dir):
        """
        Вызывается при старте плагина.
        """

    @abstractmethod
    def draw_settings(self, parent_widget, cmdr, is_beta, position):
        """
        Вызывается при отрисовки окна настроек.
        """

    @abstractmethod
    def on_settings_changed(self, cmdr, is_beta):
        """
        Вызывается в момент, когда пользователь
        сохраняет настройки.
        """

    @abstractmethod
    def on_journal_entry(self, entry):
        """
        Вызывается при появлении новой записи в логах.
        """

    @abstractmethod
    def on_cmdr_data(self, data, is_beta):
        """
        Вызывается при появлении новых данных о командире.
        """

    @abstractmethod
    def close(self):
        """
        Вызывается в момент завершения работы плагина.
        """

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """
        Сообщает, включен ли плагин.
        """

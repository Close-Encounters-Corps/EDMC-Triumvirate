# Python imports
import os
import logging
import functools
import tkinter as tk
from semantic_version import Version

# EDMC imports
import l10n
from config import appname, appversion


# Logging configuration, required by EDMC
# https://github.com/EDCD/EDMarketConnector/blob/main/PLUGINS.md#logging
plugin_name = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f'{appname}.{plugin_name}')
if not logger.hasHandlers():
    level = logging.INFO  # So logger.info(...) is equivalent to print()
    logger.setLevel(level)
    logger_channel = logging.StreamHandler()
    logger_formatter = logging.Formatter(f'%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s')
    logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
    logger_formatter.default_msec_format = '%s.%03d'
    logger_channel.setFormatter(logger_formatter)
    logger.addHandler(logger_channel)


# Translation function configuration
# https://github.com/EDCD/EDMarketConnector/blob/main/PLUGINS.md#localisation
_translate = functools.partial(l10n.translations.tl, context=__file__)


# Determining the EDMC version
EDMC_VERSION: Version = appversion() if callable(appversion) else Version(appversion)


# Функции управления, вызываемые EDMC
def plugin_start(plugin_dir):
    """
    EDMC вызывает эту функцию при запуске плагина в режиме Python 2.
    """
    raise EnvironmentError(_translate("At least EDMC 5.11.0 is required to use this plugin."))


def plugin_start3(plugin_dir):
    """
    EDMC вызывает эту функцию при запуске плагина в режиме Python 3.
    """
    if EDMC_VERSION < Version("5.11.0"):
        raise EnvironmentError(_translate("At least EDMC 5.11.0 is required to use this plugin."))
    
    #TODO: обновление, инициализация


def plugin_app(parent: tk.Misc):
    """
    EDMC вызывает эту функцию при запуске плагина для получения элемента UI плагина,
    отображаемого в окне программы.
    """
    #TODO: возврат заглушки, ожидание обновления
    pass


def plugin_stop():
    """
    EDMC вызывает эту функцию при закрытии.
    """
    #TODO: завершение с учётом механизма обновления


def plugin_prefs(parent: tk.Misc, cmdr: str | None, is_beta: bool):
    """
    EDMC вызывает эту функцию для получения вкладки настроек плагина.
    """
    #TODO: сделать с учётом механизма обновления


def prefs_changed(cmdr: str | None, is_beta: bool):
    """
    EDMC вызывает эту функцию при сохранении настроек пользователем.
    """
    #TODO: сделать с учётом механизма обновления
    

# Эти функции относятся к внутреигровым событиям.
# Если у нас пока нет загруженного плагина, мы их будем сохранять в очереди.
def journal_entry(
    cmdr:       str | None,
    is_beta:    bool,
    system:     str | None,
    station:    str | None,
    entry:      dict,
    state:      dict
):
    """
    EDMC вызывает эту функцию при появлении новой записи в логах игры.
    """
    #TODO: сделать очередь/передачу в версию


def dashboard_entry(cmdr: str | None, is_beta: bool, entry: dict):
    """
    EDMC вызывает эту функцию при обновлении игрой status.json.
    """
    #TODO: сделать


def cmdr_data(data: dict, is_beta: bool):
    """
    EDMC вызывает эту функцию при получении данных о командире с серверов Frontier.
    """
    #TODO: сделать
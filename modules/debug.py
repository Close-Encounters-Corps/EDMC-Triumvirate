import tkinter as tk
import logging
import myNotebook as nb
from sys import _getframe
from .lib.conf import config

# Подключение функции перевода от EDMC
import l10n, functools
_translate = functools.partial(l10n.translations.tl, context=__file__)


class Debug:
    log: logging.Logger = None
    debugvar = tk.BooleanVar(value=(saved if ((saved := config.get_bool("CanonnDebug")) is not None) else True))

    @classmethod
    def setup(cls, log: logging.Logger):
        cls.log = log
        cls.log.setLevel(logging.DEBUG if (cls.debugvar.get() == True) else logging.INFO)
        if config.get_bool("CanonnDebug") is None:
            config.set('CanonnDebug', cls.debugvar.get())
            cls.log.debug("CanonnDebug set to {}.".format(cls.debugvar.get()))

    @classmethod
    def info(cls, value, *args):
        if cls.log.level <= logging.INFO:
            if args:
                value = value.format(*args)
            cls.log.info(value, stacklevel=3, extra={"qualname": cls.__get_qualname()})

    @classmethod
    def debug(cls, value, *args):
        if cls.log.level <= logging.DEBUG:
            if args:
                value = value.format(*args)
            cls.log.debug(value, stacklevel=3, extra={"qualname": cls.__get_qualname()})

    @classmethod
    def error(cls, value, *args):
        if cls.log.level <= logging.ERROR:
            if args:
                value = value.format(*args)
            cls.log.error(value, stacklevel=3, extra={"qualname": cls.__get_qualname()})

    @classmethod
    def warning(cls, value, *args):
        if args:
            value = value.format(*args)
        cls.log.warning(value, stacklevel=3, extra={"qualname": cls.__get_qualname()})

    @classmethod
    def plugin_prefs(cls, parent):
        "Called to get a tk Frame for the settings dialog."
        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row=0, column=0, sticky="NSEW")
        nb.Checkbutton(frame, text=_translate("Включить отладку"), variable=cls.debugvar).grid(row=0, column=0, sticky="NW")
        return frame

    @classmethod
    def prefs_changed(cls):
        "Called when the user clicks OK on the settings dialog."
        config.set('CanonnDebug', cls.debugvar.get())
        cls.log.setLevel(logging.DEBUG if (cls.debugvar.get() == True) else logging.INFO)

    @staticmethod
    def __get_qualname():
        "Чиним неправильное определение функции, пишущей логи. Спасибо разрабам EDMC, игнорящим stacklevel."
        frame = _getframe(3)    # -> <debug>.Debug.debug -> <debug>.debug -> caller
        qualname = frame.f_code.co_qualname
        del frame               # https://docs.python.org/3.11/library/inspect.html#the-interpreter-stack
        return qualname


def debug(value, *args):
    Debug.debug(value, *args)

def error(value, *args):
    Debug.error(value, *args)

def info(value, *args):
    Debug.info(value, *args)

def warning(value, *args):
    Debug.warning(value, *args)
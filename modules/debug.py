# -*- coding: utf-8 -*-
 
import tkinter as tk
from tkinter import Frame
import logging

import datetime
import sys
import threading

import myNotebook as nb
from .lib.conf import config


class Debug:
    log: logging.Logger = None
    debugvar = tk.IntVar(value=config.getint("CanonnDebug"))

    @classmethod
    def setup(cls, log: logging.Logger):
        cls.log = log

    @classmethod
    def info(cls, value, *args):
        if cls.log.level <= logging.INFO:
            if args:
                value = value.format(*args)
            cls.log.info(value)

    @classmethod
    def debug(cls, value, *args):
        if cls.log.level <= logging.DEBUG:
            if args:
                value = value.format(*args)
            cls.log.debug(value)

    @classmethod
    def error(cls, value, *args):
        if cls.log.level <= logging.ERROR:
            if args:
                value = value.format(*args)
            cls.log.error(value)

    @classmethod
    def plugin_prefs(cls, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        cls.debugvar = tk.IntVar(value=config.getint("CanonnDebug"))
        cls.log.level = logging.DEBUG if cls.debugvar.get() == 1 else logging.INFO
        cls.debugswitch = cls.debugvar.get()

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row=0, column=0, sticky="NSEW")

        nb.Checkbutton(frame, text=_("Включить отладку"), variable=cls.debugvar).grid(row=0, column=0, sticky="NW")

        return frame

    @classmethod
    def prefs_changed(cls):
        "Called when the user clicks OK on the settings dialog."
        config.set('CanonnDebug', cls.debugvar.get())
        cls.log.level = logging.DEBUG if cls.debugvar.get() == 1 else logging.INFO


def debug(value, *args):
    Debug.debug(value, *args)


def error(value, *args):
    Debug.error(value, *args)
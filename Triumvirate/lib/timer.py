import tkinter as tk
from collections.abc import Callable
from typing import Any

from Triumvirate.core.context import PluginContext
from Triumvirate.lib.thread import Thread, ThreadExit


class Timer(Thread):
    """
    Таймер для отложенного выполнения нужных нам действий.
    В отличие от tk.after, имеет возможности:
    - досрочного выполнения
    - отмены выполнения
    - выбора, надо ли выполняться при закрытии EDMC
    - и ещё пару приятных плюшек.
    """
    def __init__(
        self,
        secs: float,
        target: Callable[[], Any],
        run_on_closing: bool = True,
        run_in_the_main_thread: bool = False,
        name: str | None = None,
        *args, **kwargs
    ):
        """
        Создаёт объект таймера. Не забудьте запустить его вызовом .start()!

        :param secs: Время в секундах до вызова *target*.
        :param target: Объект, вызываемый по истечении таймера. Любой callable object.
        :param run_on_closing: Определяет, будет ли вызван *target* при закрытии EDMC до истечения таймера.
        :param run_in_the_main_thread: Если True, объект будет вызван при помощи tk.after.\
            ОБЯЗАТЕЛЬНО используйте для операций с GUI, но НЕ используйте для длительных операций,\
            особенно включающих сетевое взаимодействие - EDMC тупо зависнет на время их выполнения.
        :param name: Позволяет переопределить имя потока таймера, в противном случае будет назначено имя по-умолчанию.
        :param args: Дополнительные позиционные параметры будут переданы в вызываемый объект.
        :param kwargs: Дополнительные именованные параметры будут переданы в вызываемый объект.\
            НЕСОВМЕСТИМО С *run_in_the_main_thread = True*.

        :raises TypeError: Если вы зачем-то передали в *target* не подлежащий вызову объект.
        :raises ValueError: Если вы указали в *secs* отрицательное значение.
        :raises ValueError: Если вы передали *kwargs* и поставили *run_in_the_main_thread = True*.\
            Увы, нативно tk.after позиционные аргументы не поддерживает, а возиться с functools мне лень. Может, позже.
        """
        if not callable(target):
            raise TypeError("target is not a callable object.")
        if kwargs and run_in_the_main_thread:
            raise ValueError("Cannot safely pass kwargs to tk.after.")
        if secs < 0:
            raise ValueError("duration can't be negative")

        super().__init__(name=(name or f"Timer before {target.__qualname__}"))
        self.duration = secs
        self.target = target
        self.run_on_closing = run_on_closing
        self.run_in_the_main_thread = run_in_the_main_thread
        self.target_args = args
        self.target_kwargs = kwargs
        self.is_active = False      # не доверяю threading.is_alive


    def do_run(self):
        self.is_active = True
        PluginContext.logger.debug(f"New timer {self.name!r}: target {self.target!r} will be called in {self.duration} seconds.")
        try:
            self.sleep(self.duration)
        except ThreadExit:      # бросается sleep-ом, если EDMC закрывается
            self.is_active = False
            if self.run_on_closing:
                PluginContext.logger.debug(
                    f"Timer {self.name!r}: detected EDMC closing, calling target {self.target!r} ahead of schedule."
                )
                self.__execute()
        else:                   # а тут мы нормально дождались окончания таймера
            self.is_active = False
            PluginContext.logger.debug(f"Timer {self.name!r}: calling target {self.target!r}, delayed by {self.duration} seconds.")
            self.__execute()


    def execute_now(self):
        """Сбрасывает таймер и досрочно выполняет отложенное действие."""
        if self.is_active:
            self.run_on_closing = False     # чтобы случайно дважды target не вызвать
            self.STOP = True
            PluginContext.logger.debug(f"Timer {self.name!r} has been stopped, calling target {self.target!r} ahead of schedule.")
            self.__execute()


    def kill(self):
        """Сбрасывает таймер с отменой выполнения отложенного действия."""
        if self.is_active:
            self.run_on_closing = False
            self.STOP = True
            PluginContext.logger.debug(f"Timer {self.name!r} has been cancelled.")


    @property
    def is_running(self) -> bool:
        return self.is_active


    def __execute(self):
        if not self.run_in_the_main_thread:
            self.target(*self.target_args, **self.target_kwargs)
        else:
            tk._default_root.after(0, self.target, *self.target_args)  # pyright: ignore[reportAttributeAccessIssue]

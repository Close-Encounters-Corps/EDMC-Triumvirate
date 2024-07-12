from typing import Callable, Any
from modules.lib.thread import Thread, ThreadExit
from modules.debug import debug

class Timer(Thread):
    """
    Таймер для отложенного выполнения нужных нам действий.
    Постоянно проверяет, не следует ли ему самоубиться, дабы не блокировать закрытие EDMC,
    чем выгодно отличается от tk.after.
    """
    def __init__(self, secs: float, target: Callable[[], Any], run_on_closing: bool = True, **kwargs):
        """
        *secs* - время в секундах до вызова *target*.

        *target* - объект, вызываемый по истечении таймера. Любой callable object.

        *run_on_closing* - следует ли нам вызвать *target*, если EDMC будет закрываться до истечения таймера.
        """
        name = kwargs.get("name", f"Timer before {target.__qualname__}")
        super().__init__(name=name, **kwargs)
        self.timeout = secs
        self.target = target
        self.run_on_closing = run_on_closing
        self.is_active = False      # не доверяю threading.is_alive
    

    def do_run(self):
        self.is_active = True
        debug("[Timer] New timer: target {!r} will be called in {} seconds.", self.target, self.timeout)
        try:
            self.sleep(self.timeout)
        except ThreadExit:      # бросается sleep-ом, если EDMC закрывается
            self.is_active = False
            if self.run_on_closing:
                self.target()
        else:                   # а тут мы нормально дождались окончания таймера
            self.is_active = False
            debug("[Timer] Calling target {!r}, delayed by {} seconds.", self.target, self.timeout)
            self.target()


    def execute_now(self):
        """Сбрасывает таймер и досрочно выполняет отложенное действие."""
        if self.is_active:
            self.run_on_closing = False     # чтобы случайно дважды target не вызвать
            self.STOP = True
            debug("[Timer.execute_now] {!r} has been stopped, calling target {!r} ahead of schedule.",
                self.name,
                self.target)
            self.target()

    
    def kill(self):
        """Сбрасывает таймер с отменой выполнения отложенного действия."""
        if self.is_active:
            self.run_on_closing = False
            self.STOP = True
            debug("[Timer.kill] {!r} has been cancelled.", self.name)
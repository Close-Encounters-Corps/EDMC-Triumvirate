from typing import Callable, Any
from modules.lib.thread import Thread, ThreadExit

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
    

    def do_run(self):
        try:
            self.sleep(self.timeout)
        except ThreadExit:      # бросается sleep-ом, если EDMC закрывается
            if self.run_on_closing:
                self.target()
        else:                   # а тут мы нормально дождались окончания таймера
            self.target()
from typing import Callable, Any
from modules.lib.thread import Thread, ThreadExit

class Timer(Thread):
    """
    Через secs секунд вызывает объект target.
    Постоянно проверяет, не следует ли ему самоубиться, дабы не блокировать закрытие EDMC,
    чем выгодно отличается от tk.after.

    Параметр on_close позволяет определить, следует ли таймеру вызвать target
    в случае закрытия EDMC до истечения времени secs (по-умолчанию True).
    """
    def __init__(self, secs: float, target: Callable[[], Any], on_close: bool = True, **kwargs):
        name = kwargs.get("name", f"Timer before {target.__qualname__}")
        super().__init__(name=name, **kwargs)
        self.timeout = secs
        self.target = target
        self.on_close = on_close
    

    def do_run(self):
        try:
            self.sleep(self.timeout)
        except ThreadExit:
            # бросается sleep-ом, если EDMC закрывается
            if self.on_close:
                self.target()
        else:
            # а тут мы нормально дождались окончания таймера
            self.target()
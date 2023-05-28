# -*- coding: utf-8 -*-
import math
import threading
import time

from ..debug import debug

class BasicThread(threading.Thread):
    """
    Обёртка над Thread'ом с различными
    дополнительными методами для управления
    пулом потоков и с возможностью их останова.
    """
    pool = []
    STOP_ALL = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        BasicThread.pool.append(self)
        # флаг для сигнализирования потоку, что ему пора бы остановиться
        self.STOP = False
        self.sleep_duration = 5

    def sleep(self, secs: float):
        cycles = math.ceil(secs / self.sleep_duration)
        for x in range(cycles):
            if self.STOP:
                raise ThreadExit()
            duration = self.sleep_duration
            if (x + 1) == cycles:
                duration = (secs % self.sleep_duration) or self.sleep_duration
            time.sleep(duration)

    @classmethod
    def stop_all(cls):
        cls.STOP_ALL = True
        for thread in cls.pool:
            thread.STOP = True

    @classmethod
    def list_alive(cls):
        return [x for x in cls.pool if x.is_alive()]

class Thread(BasicThread):
    def run(self):
        try:
            self.do_run()
            # перехватываем ThreadExit, чтобы он не попадал в лог
        except ThreadExit:
            pass
        debug("Thread {} shutted down", self.name)

    def do_run(self):
        raise NotImplementedError()


class ThreadExit(Exception):
    """
    Исключение, которое используется для прерывания потока.
    """

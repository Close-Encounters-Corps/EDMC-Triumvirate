# -*- coding: utf-8 -*-
import threading

class Thread(threading.Thread):
    """
    Обёртка над Thread'ом с различными
    дополнительными методами для управления
    пулом потоков и с возможностью их останова.
    """
    pool = []
    STOP_ALL = False

    def __init__(self, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        Thread.pool.append(self)
        # флаг для сигнализирования потоку, что ему пора бы остановиться
        self.STOP = False

    @classmethod
    def stop_all(cls):
        cls.STOP_ALL = True
        for thread in cls.pool:
            thread.STOP = True

    @classmethod
    def list_alive(cls):
        return [x for x in cls.pool if x.is_alive()]

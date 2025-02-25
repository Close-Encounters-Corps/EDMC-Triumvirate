from modules.lib.module import Module


# Изначально предполагалось, что эта штука будет в model.py,
# но из-за проблемы рекурсивного импорта пришлось вынести её в отдельный файл.

class _DataItem:
    def __init__(self, module: Module, category: str, location: str, text: str):
        self.m_qualname = module.__class__.__qualname__
        self.category   = category
        self.location   = location
        self.text       = text

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, _DataItem):
            return NotImplemented
        if self.category != other.category:
            return self.category < other.category
        if self.location != other.location:
            return self.location < other.location
        return self.text < other.text

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _DataItem):
            return NotImplemented
        # одинаковую инфу из разных модулей будем считать равной - это нужно для упрощения кода ui
        return (self.category, self.location, self.text) == (other.category, other.location, other.text)

    def __hash__(self) -> int:
        # аналогично - модуль-источник не будет давать уникальности
        return hash((self.category, self.location, self.text))

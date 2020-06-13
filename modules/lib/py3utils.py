"""
Классы и функции, связанные с поддержкой Python 3.
"""

class BytesDecoder:
    """Обёртка итератора, 'на лету' декодирующая текст из байтов."""
    def __init__(self, stream):
        self.stream = stream

    def __iter__(self):
        for line in self.stream:
            yield line.decode()

import csv
import requests
from contextlib import closing

from Triumvirate.core.context import PluginContext


class BytesDecoder:
    def __init__(self, stream):
        self.stream = stream

    def __iter__(self):
        for line in self.stream:
            line = line.decode()
            # debug(f"Processing {line}")
            yield line


class Spreadsheet:
    def __init__(self, url):
        self.url = url
        self.response = None
        self.data = None

    def download(self):
        with closing(requests.get(self.url, stream=True, timeout=5)) as resp:
            if not resp.ok:
                PluginContext.logger.debug(f"Original URL: {self.url}")
                PluginContext.logger.debug(f"Spreadsheets response: {resp}:\n{resp.text}")
                raise AssertionError(f"Response from Google Spreadsheets ({resp.request.url!r}) is not OK.")
            self.response = resp
            self.process()

    def process(self):
        # почему генератор списка вместо тупо list()?
        # потому что list() зачем-то вызывает len(),
        # который снова вызывает load_all, и получается рекурсия
        self.data = [x for x in self]

    def __iter__(self):
        if not self.response:
            self.download()
        stream = BytesDecoder(self.response.raw)  # pyright: ignore[reportOptionalMemberAccess]
        reader = csv.reader(stream)
        try:
            next(reader)    # пропускаем заголовок
        except StopIteration:   # ну и ладно...
            pass
        yield from reader

    def __getitem__(self, num):
        if self.data is None:
            self.download()
        return self.data[num]  # pyright: ignore[reportOptionalSubscript]

    def __len__(self):
        if self.data is None:
            self.download()
        return len(self.data)  # pyright: ignore[reportArgumentType]

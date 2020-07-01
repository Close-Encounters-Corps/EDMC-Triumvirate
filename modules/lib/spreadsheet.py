import csv
from contextlib import closing

import requests
from ..debug import debug

class BytesDecoder:
    def __init__(self, stream):
        self.stream = stream

    def __iter__(self):
        for line in self.stream:
            line = line.decode()
            # debug("Processing {}", line)
            yield line

class Spreadsheet:
    def __init__(self, url):
        self.url = url
        self.response = None
        self.data = None

    def download(self):
        with closing(requests.get(self.url, stream=True)) as resp:
            if not resp.ok:
                debug("Spreadsheets response: {}:\n{}", resp, resp.text)
                raise AssertionError(
                    f"Response from Google Spreadsheets ({resp.request.url!r}) is not OK."
                )
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
        stream = BytesDecoder(self.response.raw)
        reader = csv.reader(stream)
        try:
            next(reader) # пропускаем заголовок
        except StopIteration: # ну и ладно...
            pass
        yield from reader

    def __getitem__(self, num):
        if self.data is None:
            self.download()
        return self.data[num]

    def __len__(self):
        if self.data is None:
            self.download()
        return len(self.data)

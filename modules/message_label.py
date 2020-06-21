import tkinter as tk

class MessageLabel(tk.Label):
    def __init__(self, *args, row=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.showed = False
        self._row = row

    @property
    def text(self):
        return self["text"]

    @text.setter
    def text(self, value):
        self["text"] = value
        if not self.showed:
            self.grid(row=self._row, column=0, sticky=tk.EW + tk.N)
            self.showed = True

    def clear(self):
        self.grid()
        self.showed = False

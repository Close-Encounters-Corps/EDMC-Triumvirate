import tkinter as tk

class MessageLabel(tk.Label):
    def __init__(self, *args, row=0, **kwargs):
        super().__init__(*args, justify="left", **kwargs)
        self.showed = False
        self._row = row

    @property
    def text(self):
        return self["text"]

    @text.setter
    def text(self, value):
        main_window: tk.Tk = tk._default_root
        main_window.update()
        maxlen = 300 if main_window.winfo_width() <= 300 else main_window.winfo_width()
        self.configure(wraplength=maxlen)

        self["text"] = value
        if not self.showed:
            self.grid(row=self._row, column=0, sticky="nw")
            self.showed = True

    def clear(self):
        self.grid_forget()
        self.showed = False
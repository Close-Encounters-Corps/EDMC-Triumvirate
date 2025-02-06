import tkinter as tk
from tkinter import ttk
from pathlib import Path
from PIL import Image, ImageTk

from context import PluginContext
from modules.lib.timer import Timer


class _Message(tk.Frame):
    _cross_image: ImageTk.PhotoImage | None = None

    def __init__(self, master, text: str, timeout: int):
        super().__init__(master, relief="groove")
        self.grid_columnconfigure(0, weight=1)

        self._label = ttk.Label(self, text=text, wraplength=self._get_wraplength())
        self._label.grid(row=0, column=0, pady=2, sticky="w")

        if not self._cross_image:
            self._set_image()
        self._button = ttk.Button(self, image=self._cross_image, command=self._close)
        self._button.grid(row=0, column=1, padx=5, pady=2, sticky="e")

        self.pack(side="top", fill="x")

        if timeout != 0:
            self._timer = Timer(timeout, self._close, run_on_closing=False, run_in_the_main_thread=True)
            self._timer.start()
        else:
            self._timer = None


    def _close(self):
        if self._timer:
            self._timer.kill()      # на случай, если уведомление скрыто раньше времени
        self.destroy()
        self.master._message_destroyed(self)

    @classmethod
    def _set_image(cls):
        size = int(16 * (tk._default_root.winfo_screenheight() / 1080))
        image = Image.open(Path(PluginContext.plugin_dir)/'icons'/'cross.png')
        image = image.resize((size, size))
        cls._cross_image = ImageTk.PhotoImage(image)

    @staticmethod
    def _get_wraplength():
        main_window: tk.Tk = tk._default_root
        main_window.update()
        return 275 if main_window.winfo_width() <= 275 else main_window.winfo_width()


class Notifier(tk.Frame):
    """
    Фрейм с текстовыми уведомлениями пользователю. Замена древней message_label.
    Поддерживает несколько одновременных уведомлений, их скрытие пользователем по нажатию кнопки
    или плагином по истечении определённого промежутка времени.
    """

    MAX_NOTIFICATIONS = 5

    def __init__(self, parent, row):
        super().__init__(parent)
        self.gridrow = row
        self._pool: list[_Message] = list()


    def send(self, text: str, timeout: int = 60):
        """
        Выводит новое уведомление.

        *text* - очевидно, текст уведомления.

        *timeout* - промежуток времени, спустя который уведомление автоматически скроется.
        Можно задать 0, тогда оно будет висеть, пока пользователь сам его не закроет.
        """
        self.after(0, self.__send, text, timeout)


    def clear(self):
        """Очищает фрейм, удаляя все уведомления."""
        self.after(0, self.__clear)


    def __send(self, text, timeout):
        if len(self._pool) == 0:
            self.__show()
        elif len(self._pool) == self.MAX_NOTIFICATIONS:
            self._pool[0]._close()
        self._pool.append(_Message(self, text, timeout))


    def __clear(self):
        for message in self._pool:
            message._close()
        self.__hide()


    def _message_destroyed(self, message: _Message):
        """Метод, вызываемый скрытыми сообщения при удаления их из списка."""
        self._pool.remove(message)
        if len(self._pool) == 0:
            self.__hide()


    def __show(self):
        if len(self._pool) > 0:
            self.grid(row=self.gridrow, column=0, sticky="NWSE")

    def __hide(self):
        self.grid_forget()

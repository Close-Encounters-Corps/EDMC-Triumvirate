import tkinter as tk
from PIL import Image, ImageTk
from semantic_version import Version

from Triumvirate.lib.ui_utils import AutohidingFrame
import myNotebook as nb  # type: ignore
from theme import theme  # type: ignore

from Triumvirate.core.context import PluginContext
from Triumvirate.lib.timer import Timer


class _Message(tk.Frame):
    _cross_image: ImageTk.PhotoImage
    _cross_image_white: ImageTk.PhotoImage

    def __init__(self, master: 'Notifier', text: str, timeout: int):
        self._notifier = master
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        self._label = tk.Label(self, text=text, justify="left", wraplength=self._get_wraplength())
        self._label.grid(row=0, column=0, pady=2, sticky="W")

        self._button = nb.Button(self, image=self._cross_image)
        self._button_dark = tk.Label(self, image=self._cross_image_white)
        grid_params = {"row": 0, "column": 1, "padx": 5, "pady": 2, "sticky": "E"}
        theme.register_alternate(
            (self._button, self._button_dark, self._button_dark),
            grid_params
        )
        self._button.bind('<Button-1>', self._close)
        theme.button_bind(self._button_dark, self._close)
        if theme.active == theme.THEME_DEFAULT:  # светлая тема
            self._button.grid(**grid_params)
        else:
            self._button_dark.grid(**grid_params)

        theme.update(self)
        self.pack(side="top", fill="x")

        if timeout != 0:
            self._timer = Timer(timeout, self._close, run_on_closing=False, run_in_the_main_thread=True)
            self._timer.start()
        else:
            self._timer = None

    def _close(self, event: tk.Event | None = None):
        if self._timer:
            self._timer.kill()  # на случай, если уведомление скрыто раньше времени

        # Это сделано для обхода бага в EDMC 6.0 - https://github.com/EDCD/EDMarketConnector/issues/2555
        # TODO: вернуть destroy с версии, когда будет выпущен фикс
        if PluginContext.edmc_version >= Version("6.0.0"):
            self.pack_forget()
        else:
            self.destroy()

        self._notifier._pool.remove(self)

    @classmethod
    def _set_images(cls):
        size = int(14 * (tk._default_root.winfo_screenheight() / 1080))  # pyright: ignore[reportAttributeAccessIssue]
        image = Image.open(PluginContext.paths.assets_dir / "icons" / "cross.png")
        image = image.resize((size, size))
        cls._cross_image = ImageTk.PhotoImage(image)
        image_white = Image.open(PluginContext.paths.assets_dir / "icons" / "cross_white.png")
        image_white = image_white.resize((size, size))
        cls._cross_image_white = ImageTk.PhotoImage(image_white)

    @staticmethod
    def _get_wraplength():
        main_window: tk.Tk = tk._default_root  # pyright: ignore[reportAttributeAccessIssue]
        main_window.update()
        return max(main_window.winfo_width(), 300)


class Notifier(AutohidingFrame):
    """
    Фрейм с текстовыми уведомлениями пользователю. Замена древней message_label.
    Поддерживает несколько одновременных уведомлений, их скрытие пользователем по нажатию кнопки
    или плагином по истечении определённого промежутка времени.
    """

    MAX_NOTIFICATIONS = 5

    def __init__(self, parent: tk.Widget, row: int):
        super().__init__(parent, grid_options={'row': row, 'column': 0, 'sticky': 'NWSE'})
        _Message._set_images()
        self._pool: list[_Message] = []


    def display(self, text: str, timeout: int = 60):
        """
        Выводит новое уведомление.

        *text* - очевидно, текст уведомления.

        *timeout* - промежуток времени, спустя который уведомление автоматически скроется.
        Можно задать 0, тогда оно будет висеть, пока пользователь сам его не закроет.
        """
        self.after(0, self.__display, text, timeout)


    def clear(self):
        """Очищает фрейм, удаляя все уведомления."""
        self.after(0, self.__clear)


    def __display(self, text, timeout):
        if len(self._pool) == self.MAX_NOTIFICATIONS:
            self._pool[0]._close()
        self._pool.append(_Message(self, text, timeout))

    def __clear(self):
        for message in self._pool:
            message._close()

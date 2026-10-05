import tkinter as tk
from tkinter import font as tk_font

from theme import theme  # type: ignore

from Triumvirate.core.context import PluginContext


class Table(tk.Frame):
    """
    Крайне ленивая имплементация виджета таблицы.
    В отличие от tk.TreeView, занимает как можно меньше места и поддерживает многострочность.
    """
    MAXWIDTH = 500

    def __init__(self, parent: tk.Misc, headers: list[str], *args, **kwargs):
        self.tkfont_instance = tk_font.Font()
        self.border_color = kwargs.get("border_color", "black")

        super().__init__(parent, highlightthickness=1, highlightbackground=self.border_color, *args, **kwargs)

        self.headers = headers
        self.__columns: list[tk.Label] = []
        for i in range(len(headers)):
            self.columnconfigure(i, weight=1)
            f = tk.Frame(self, highlightthickness=1, highlightbackground=self.border_color)
            f.grid(row=0, column=i, sticky="NWSE")
            self.__columns.append(tk.Label(f, text=headers[i]))
            self.__columns[i].pack(padx=3, fill="both")

        self.__n_columns = len(self.__columns)
        self.__current_row = 1
        self.__cells: list[tk.Frame] = []


    def insert(self, *values):
        values = list(values)
        if len(values) != self.__n_columns:
            raise RuntimeError()

        max_width = max(self.MAXWIDTH, tk._default_root.winfo_width())  # pyright: ignore[reportAttributeAccessIssue]
        max_string_len = int(self.MAXWIDTH / len(values))
        used_width = 0

        for i, val in enumerate(values):
            frame = tk.Frame(self, highlightthickness=1, highlightbackground=self.border_color)

            if i == len(values) - 1:
                max_string_len = max(max_string_len, max_width - used_width)
            label = tk.Label(frame, text=val, wraplength=max_string_len)
            label.pack(padx=3, fill="x")
            used_width += self.measure_longest_line(label["text"])

            frame.grid(row=self.__current_row, column=i, sticky="NWSE")
            theme.update(frame)
            self.__cells.append(frame)

        self.__current_row += 1


    def clear(self):
        for frame in self.__cells:
            frame.destroy()
        self.__current_row = 1


    def measure_longest_line(self, text: str) -> int:
        """Обёртка над tk.font.Font().measure(), но возвращающая значение для самой длинной строки текста."""
        lines = text.split('\n')
        measures = [self.tkfont_instance.measure(line) for line in lines]
        return max(measures)


class AutohidingFrame(tk.Frame):
    """
    `tk.Frame`, но автоматически скрывающийся, если все его потомки также скрыты.
    Обычный фрейм при анмапе последнего потомка не меняет свой размер и остаётся висеть пустым
    местом на экране.
    Разумеется, при маппинге хотя бы одного потомка также возвращается на экран.

    Потомки могут использовать любой из менеджеров геометрии. Сам фрейм ограничен grid-ом для упрощения кода.
    """
    class _ChildrenWatcherDict(dict):
        def __init__(self, frame_instance: 'AutohidingFrame'):
            super().__init__()
            self._frame_instance = frame_instance

        def __setitem__(self, key: str, value: tk.Widget) -> None:
            super().__setitem__(key, value)
            self._frame_instance._patch_child(value)

        def __delitem__(self, key: str):
            # Вызывается при уничтожении виджета. Вроде как надёжнее, чем оборачивать .destroy()
            super().__delitem__(key)
            self._frame_instance._check_visibility()


    def __init__(self, master: tk.Misc, grid_options: dict, **kwargs):
        super().__init__(master, **kwargs)
        self.__grid_options = grid_options
        self.__shown = False
        # Ключ к магии: каждый виджет имеет аттрибут children - словарь, куда сами себя вносят потомки
        # при создании (в своём __init__). Мы же с помощью кастомного класса будем перехватывать
        # изменения этого словаря - то есть моменты создания потомков - и добавлять обёртки к их методам
        # геометрии, чтобы при их вызове потомки также обновляли наше состояние.
        self.children = self._ChildrenWatcherDict(self)


    def _patch_child(self, child: tk.Widget):
        show_methods = ('grid', 'grid_configure', 'pack', 'pack_configure', 'place', 'place_configure')
        hide_methods = ('grid_remove', 'grid_forget', 'pack_forget', 'place_forget')
        for name in show_methods + hide_methods:
            if hasattr(child, name):
                def make_wrapper(orig):
                    def wrapper(*args, **kwargs):
                        res = orig(*args, **kwargs)
                        self._check_visibility()
                        return res
                    return wrapper
                orig_method = getattr(child, name)
                setattr(child, name, make_wrapper(orig_method))


    def _check_visibility(self):
        try:
            if not self.winfo_exists():
                return
            has_visible_children = any(
                bool(child.winfo_manager()) for child in self.children.values()
            )
            if has_visible_children and not self.__shown:
                self.grid(**self.__grid_options)
                self.__shown = True
            elif not has_visible_children and self.__shown:
                self.grid_remove()
                self.__shown = False
        except tk.TclError as e:
            PluginContext.logger.error("Tkinter exception during handling an AutohidingFrame's child mapping change:", exc_info=e)

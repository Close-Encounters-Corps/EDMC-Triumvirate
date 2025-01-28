import tkinter as tk
from tkinter import font as tk_font


class Table(tk.Frame):
    """
    Крайне ленивая имплементация виджета таблицы.
    В отличие от tk.TreeView, занимает как можно меньше места и поддерживает многострочность.
    """
    MAXWIDTH = 500

    def __init__(self, parent: tk.Misc, headers: list[str], *args, **kwargs):
        self.tkfont_instance = tk_font.Font()

        self.bg = kwargs.get("bg") or kwargs.get("background") or "white"
        self.relief = "solid"
        kwargs.pop("bg", None)
        kwargs.pop("background", None)
        kwargs.pop("relief", None)
        kwargs.pop("borderwidth", None)

        super().__init__(parent, bg=self.bg, relief=self.relief, borderwidth=1, *args, **kwargs)

        self.headers = headers
        self.__columns: list[tk.Label] = []
        for i in range(len(headers)):
            self.columnconfigure(i, weight=1)
            f = tk.Frame(self, bg=self.bg, relief=self.relief, borderwidth=1)
            f.grid(row=0, column=i, sticky="NWSE")
            self.__columns.append(tk.Label(f, text=headers[i], bg=self.bg))
            self.__columns[i].pack(padx=3, fill="both")
        
        self.__n_columns = len(self.__columns)
        self.__current_row = 1
        self.__cells: list[tk.Frame] = []


    def insert(self, *values):
        values = list(values)
        if len(values) != self.__n_columns:
            raise RuntimeError()
        
        max_width = max(self.MAXWIDTH, tk._default_root.winfo_width())
        max_string_len = int(self.MAXWIDTH / len(values))
        used_width = 0
        
        for i, val in enumerate(values):
            f = tk.Frame(self, bg=self.bg, relief=self.relief, borderwidth=1)
            f.grid(row=self.__current_row, column=i, sticky="NWSE")

            if i == len(values)-1:
                max_string_len = max(max_string_len, max_width-used_width)
            l = tk.Label(f, text=val, bg=self.bg, wraplength=max_string_len)
            l.pack(padx=3, expand=True)

            used_width += self.measure_longest_line(l["text"])
            self.__cells.append(f)

        self.__current_row += 1
    
    
    def clear(self):
        for l in self.__cells:  l.destroy()
        self.__current_row = 1
        

    def measure_longest_line(self, text: str) -> int:
        """Обёртка над tk.font.Font().measure(), но возвращающая значение для самой длинной строки текста."""
        lines = text.split('\n')
        measures = [self.tkfont_instance.measure(line) for line in lines]
        return max(measures)


    def wrap_text(self, text: str, max_width: int) -> str:
        """
        Аналог wraplength из tk.Label, но для случаев, где его применение невозможно.
        Бьёт текст на строки так, чтобы они не превышали по ширине заданного значения.
        """
        words = text.split()
        result = ''
        current_line = ''
        for word in words:
            test_line = current_line + ('' if current_line == '' else ' ') + word
            if self.tkfont_instance.measure(test_line) > max_width:
                # проверка на исключительный случай
                if self.tkfont_instance.measure(word) > max_width:
                    # кто-то балуется с нечитаемо длинным текстом
                    result += current_line + ('' if current_line == '' else '\n') + word + '\n'
                else:
                    result += current_line + '\n'
                    current_line = word
            else:
                current_line = test_line
        result += current_line
        return result
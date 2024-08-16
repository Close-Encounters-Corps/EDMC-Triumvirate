import re
import tkinter as tk
from tkinter import PhotoImage
from pathlib import Path

from modules.debug import warning, debug
from modules.lib.module import Module

from tkinter import ttk as nb
# import myNotebook as nb
from l10n import translations as tr


CATEGORIES = [
    "Anomaly",
    "Biology",
    "Cloud",
    "Geology",
    "Guardian",
    "Human",
    "Other",
    "Planets",
    "Ring",
    "Thargoid",
    "Tourist",
    "None"
]


class _DataItem:
    DEFAULT_CATEGORY = "None"
    _BODY_PATTERN = re.compile(r"([A-Z]+\s)*\d+(\s[a-z])*$")

    def __init__(self, category: str, body: str, text: str, no_shrink: bool):
        """
        Контейнер для хранения информации по POI, предназначенной к отображению.
        """
        if not category in CATEGORIES:
            warning(f'[Visualizer] Unknown category "{category}", setting to default value ("{self.DEFAULT_CATEGORY}")')
            category = self.DEFAULT_CATEGORY
        
        if not no_shrink:
            re_match = re.search(self._BODY_PATTERN, body)
            if re_match:
                # нам дали название тела вместе с именем системы - уберём лишнее
                body = re_match.group(1)
        
        self.category = category
        self.body = body
        self.text = text
    
    def __lt__(self, other):
        return self.category < other.category or self.body < other.body



class _ModuleGroup(nb.Frame):
    """Элементы отображения отдельного модуля в настройках визуализатора."""

    def __init__(self, parent: tk.Misc, module: Module, enabled: bool):
        super().__init__(parent)
        self.__module = module
        self.name_label = nb.Label(self, text=module.localized_name, justify='left')
        self.status_var = tk.BooleanVar(value=enabled)
        self.checkbox   = nb.Checkbutton(self, variable=self.status_var)
        self.checkbox.pack(side='left')
        self.name_label.pack(side='left')

    def change_state(self, new_state):
        self.name_label.configure(state=new_state)
        self.checkbox.configure(state=new_state)

    @property
    def enabled(self):
        return self.status_var.get()
    
    @property
    def module_qualname(self):
        return self.__module.__class__.__qualname__



class _VisualizerSettingsFrame(nb.Frame):
    """Фрейм настроек визуализатора."""

    def __init__(self, vis_instance: Module, parent: tk.Misc, row: int):
        super().__init__(parent)
        modules = vis_instance.get_registered_modules()
        self.modules_frames = [_ModuleGroup(self, module, vis_instance.is_module_enabled(module)) for module in modules]

        self.info_label = nb.Label(self, text=tr.tl("Visualizer settings:"))
        self.info_label.pack(side='top', fill='x')

        self.vis_frame = nb.Frame(self)
        self.vis_label = nb.Label(self.vis_frame, text=tr.tl("Show visualizer module: "))
        self.vis_checkbox_var = tk.BooleanVar(self.vis_frame, value=vis_instance.enabled)
        self.vis_checkbox = nb.Checkbutton(self.vis_frame, variable=self.vis_checkbox_var, command=self.__change_groups_state)
        self.vis_label.pack(side='left')
        self.vis_checkbox.pack(side='left')
        self.vis_frame.pack(side='top', fill='x')

        self.delimeter_label = nb.Label(self, text=tr.tl("Show output from selected modules:"))
        self.delimeter_label.pack(side='top', fill='x')

        for frame in self.modules_frames:
            frame.pack(side='top', fill='x')
        self.__change_groups_state()

        self.grid(column=0, row=row)

    def __change_groups_state(self):
        new_state = "normal" if self.vis_checkbox_var.get() == True else "disabled"
        for frame in self.modules_frames:
            frame.change_state(new_state)
        self.delimeter_label.configure(state=new_state)

    def get_current_config(self) -> dict[str, bool]:
        config = dict()
        for module in self.modules_frames:
            config[module.module_qualname] = module.enabled
        return config
    


class _IconButton(nb.Button):
    def __init__(self, parent, category, plugin_dir, callback):
        super().__init__(parent)
        self.category = category
        self.__callback = callback

        icons_path = Path(plugin_dir, "icons")
        self.active_icon =  PhotoImage(name=f"{category}_active", file=icons_path / f"{category}.gif")
        self.grey_icon =    PhotoImage(name=f"{category}_grey", file=icons_path / f"{category}_grey.gif")

        self.disable()
        self.configure(command=self.__on_click)
    

    def acticate(self):
        self.configure(image=self.active_icon)
        self.visible_state = "active"
    
    def deactivate(self):
        self.configure(image=self.grey_icon)
        self.visible_state = "disabled"

    def __on_click(self):
        self.__callback(self.category)
        


class _VisualizerFrame(nb.Frame):
    """
    Собственно отображаемая часть визуализатора.
    """

    def __init__(self, parent: tk.Misc, row: int, shown: bool, plugin_dir: str):
        self.__active_ctg: str | None = None
        self.__shown: bool = shown
        # забудьте, что видели эти аттрибуты.
        # все взаимодействия через self.active_category и self.shown соответственно

        super().__init__(parent)
        self.plugin_dir = plugin_dir
        self.row = row
        self.system_data: dict[str, list[_DataItem]] = {}

        self.buttons_frame = nb.Frame(self)
        self.buttons: dict[str, _IconButton] = []
        for ctg in CATEGORIES:
            self.buttons[ctg] = _IconButton(self.buttons_frame, ctg, plugin_dir, self.__button_callback)
        self.buttons_frame.pack(side='top', fill='x')

        self.category_frame = nb.Frame(self)
        self.category_text_label = nb.Label(self.category_frame, text=tr.tl("Shown category:"))
        self.category_text_label.pack(side='left', padx=5)
        self.active_category_label = nb.Label(self.category_frame)  # текст обновляется в active_category()
        self.active_category_label.pack(side='left')

        self.details_frame = nb.Frame(self)
    

    def add_data(self, data: _DataItem):
        self.system_data[data.category].append(data)
        if self.active_category == data.category:
            # надо обновить отображаемые данные
            self.__show_details(data.category)

    
    def clear(self):
        self.active_category = None
        self.system_data.clear()


    @property
    def active_category(self):
        return self.__active_ctg
    

    @active_category.setter
    def active_category(self, ctg: str | None):
        old_ctg = self.__active_ctg
        self.__active_ctg = ctg
        self.buttons[old_ctg].deactivate()

        if ctg == None:
            self.category_frame.pack_forget()
            self.details_frame.pack_forget()
        else:
            self.buttons[ctg].activate()
            self.active_category_label.configure(text=tr.tl(ctg))
            self.__show_details(ctg)
            if old_ctg == None:
                self.category_frame.pack(side='top', fill='x')
                self.details_frame.pack(side='top', fill='x')

    
    @property
    def shown(self):
        return self.__shown
    

    @shown.setter
    def shown(self, val: bool):
        if val == True:
            self.grid(column=0, row=self.row)
        else:
            self.grid_forget()


    def __button_callback(self, category):
        if category == self.active_category:
            self.active_category = None
        else:
            self.active_category = category


    def __show_details(self, category):
        class Row(nb.Frame):
            def __init__(self, parent, body, info, row):
                super().__init__(parent)
                self.b_label = nb.Label(self, text=body)
                self.i_label = nb.Label(self, text=info)    # перевод на совести модуля-отправителя инфы
                self.b_label.grid(column=0, row=row, padx=3)
                self.i_label.grid(column=1, row=row, padx=3)

        self.__details_rows = list()
        data = self.system_data[category]
        data.sort()
        for i, item in enumerate(data):
            row = Row(self.details_frame, item.body, item.text, i)
            row.pack(side='top', fill='x')
            self.__details_rows.append(row)
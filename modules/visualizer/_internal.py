import re
import tkinter as tk
from tkinter import PhotoImage, ttk
from pathlib import Path

from modules.debug import warning
from modules.lib.conf import config as plugin_config
from modules.lib.module import Module

import myNotebook as nb
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

    def __init__(self, module: Module, category: str, body: str, string: str, no_shrink: bool = False):
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
                body = re_match.group()
        
        self.module = module.__class__.__qualname__
        self.category = category
        self.body = body
        self.info = string
    
    def __lt__(self, other):
        if self.category != other.category:
            return self.category < other.category
        if self.body != other.body:
            return self.body < other.body
        return self.info < other.info



class _ModuleGroup(tk.Frame):
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



class _VisualizerSettingsFrame(tk.Frame):
    """Фрейм настроек визуализатора."""

    def __init__(self, vis_instance: Module, parent: tk.Misc, row: int):
        super().__init__(parent, bg='white')
        modules = vis_instance.get_registered_modules()
        self.modules_frames = [_ModuleGroup(self, module, vis_instance.is_module_enabled(module)) for module in modules]

        self.vis_frame = tk.Frame(self, bg='white')
        self.vis_label = nb.Label(self.vis_frame, text=tr.tl("Show visualizer module:"))
        self.vis_checkbox_var = tk.BooleanVar(self.vis_frame, value=vis_instance.shown)
        self.vis_checkbox = nb.Checkbutton(self.vis_frame, variable=self.vis_checkbox_var, command=self.__change_groups_state)
        self.vis_label.grid(column=0, row=0)
        self.vis_checkbox.grid(column=1, row=0, padx=5)
        self.vis_frame.pack(side='top', fill='x')

        self.delimeter_label = nb.Label(self, text=tr.tl("Show output from selected modules only:"))
        self.delimeter_label.pack(side='top', anchor='w')
        self.modules_dummy_label = nb.Label(self, text=tr.tl("[No registered modules found]"))
        if len(self.modules_frames) == 0:
            self.modules_dummy_label.pack(side='left', anchor='w')
        for frame in self.modules_frames:
            frame.pack(side='top', anchor='w')
        self.__change_groups_state()

        self.grid(column=0, row=row, sticky="NWSE")

    def __change_groups_state(self):
        new_state = "normal" if self.vis_checkbox_var.get() == True else "disabled"
        for frame in self.modules_frames:
            frame.change_state(new_state)
        self.delimeter_label.configure(state=new_state)
        self.modules_dummy_label.configure(state=new_state)

    def get_current_config(self) -> tuple[bool, dict[str, bool]]:
        vis_enabled = self.vis_checkbox_var.get()
        config = dict()
        for module in self.modules_frames:
            config[module.module_qualname] = module.enabled
        return vis_enabled, config
    


class _IconButton(nb.Button):
    def __init__(self, parent, category, plugin_dir, callback):
        super().__init__(parent)
        self.category = category
        self.__callback = callback

        icons_path = Path(plugin_dir, "icons")
        self.active_icon = PhotoImage(file=icons_path / f"{category}.gif")
        self.grey_icon = PhotoImage(file=icons_path / f"{category}_grey.gif")

        self.deactivate()
        self.configure(command=self.__on_click)
    

    def activate(self):
        self.configure(image=self.active_icon)
    
    def deactivate(self):
        self.configure(image=self.grey_icon)

    def __on_click(self):
        self.__callback(self.category)
        


class _VisualizerFrame(tk.Frame):
    """
    Собственно отображаемая часть визуализатора.
    """

    def __init__(self, parent: tk.Misc, row: int, shown: bool, plugin_dir: str, config: dict[str, bool]):
        self.__active_ctg: str | None = None
        self.__shown: bool = None
        # забудьте, что видели эти аттрибуты.
        # все взаимодействия через self.active_category и self.shown соответственно

        super().__init__(parent)
        self.plugin_dir = plugin_dir
        self.row = row
        self.system_data: dict[str, list[_DataItem]] = {}       # с разбивкой по категориям

        self.buttons_frame = tk.Frame(self)
        self.buttons_dummy_label = ttk.Label(self.buttons_frame, text=tr.tl("Waiting for data..."))
        self.buttons_dummy_label.pack(side='top', fill='x')
        self.buttons: dict[str, _IconButton] = {}
        for ctg in CATEGORIES:
            self.buttons[ctg] = _IconButton(self.buttons_frame, ctg, plugin_dir, self.__button_callback)
        self.buttons_frame.pack(side='top', fill='x')

        self.category_frame = tk.Frame(self)
        self.category_text_label = ttk.Label(self.category_frame, text=tr.tl("Displayed category:"))
        self.category_text_label.pack(side='left')
        self.active_category_label = ttk.Label(self.category_frame)  # текст обновляется в active_category.setter
        self.active_category_label.pack(side='left', padx=3)

        self.details_frame = tk.Frame(self)
        self.details_body_header_label = ttk.Label(self.details_frame, text=tr.tl("Body"))
        self.details_info_header_label = ttk.Label(self.details_frame, text=tr.tl("POI"))
        self.details_body_header_label.grid(row=0, column=0)
        self.details_info_header_label.grid(row=0, column=1)

        self.enabled_modules = [module for module, enabled in config.items() if enabled]
        self.shown = shown
    

    def add_data(self, data: _DataItem):
        newCategory = (self.system_data.get(data.category) == None)
        if newCategory:
            self.system_data[data.category] = []
            self.after(0, self.__update_buttons_frame)
        self.system_data[data.category].append(data)
        if self.active_category == data.category:
            self.after(0, self.__update_details_frame)

    
    def clear(self):
        self.system_data.clear()
        self.after(0, self.__clear)
    

    def update_config(self, new_config: dict[str, bool]):
        self.enabled_modules = [module for module, enabled in new_config.items() if enabled]
        print(self.enabled_modules)
        self.active_category = None     # здесь же обновится self.details_frame
        self.after(0, self.__update_buttons_frame)


    @property
    def active_category(self):
        return self.__active_ctg
    

    @active_category.setter
    def active_category(self, ctg: str | None):
        old_ctg = self.__active_ctg
        self.__active_ctg = ctg
        if old_ctg is not None:
            self.after(0, self.buttons[old_ctg].deactivate())

        if ctg != None:
            self.after(0, self.buttons[ctg].activate())
        self.after(0, self.__update_details_frame)

    
    @property
    def shown(self):
        return self.__shown
    

    @shown.setter
    def shown(self, val: bool):
        self.after(0, self.__change_visibility, val)
        self.__shown = val


    def __button_callback(self, category):
        if category == self.active_category:
            self.active_category = None
        else:
            self.active_category = category
    

    def __update_buttons_frame(self):
        self.buttons_dummy_label.pack_forget()
        for _, button in self.buttons.items():
            button.pack_forget()

        if len(self.system_data.keys()) == 0:
            self.buttons_dummy_label.pack(side='top', fill='x')
            return
        
        buttons_to_map = []
        for ctg, items in self.system_data.items():
            if any(item.module in self.enabled_modules for item in items):
                buttons_to_map.append(self.buttons[ctg])

        if len(buttons_to_map) == 0:
            self.buttons_dummy_label.pack(side='top', fill='x')
        else:
            for button in buttons_to_map:
                button.pack(side='left')
    

    def __update_details_frame(self):
        class Row:
            def __init__(self, parent, row, body, info):
                self.b_label = ttk.Label(parent, text=body)
                self.i_label = ttk.Label(parent, text=info)    # перевод на совести модуля-отправителя инфы
                self.b_label.grid(column=0, row=row, padx=3)
                self.i_label.grid(column=1, row=row, padx=3)
        
        if self.active_category == None:
            self.category_frame.pack_forget()
            self.details_frame.pack_forget()
            return
        
        if not self.details_frame.winfo_ismapped():
            self.category_frame.pack(side='top', fill='x')
            self.details_frame.pack(side='top', fill='x')
        
        self.active_category_label.configure(text=tr.tl(self.active_category))

        # очищаем существующие записи
        for item in self.details_frame.winfo_children():
            if item.grid_info()['row'] > 0:         # мы хотим оставить header-ы
                item.destroy()
        
        data = self.system_data[self.active_category]
        data.sort()
        for i, item in enumerate(data):
            if item.module in self.enabled_modules:
                Row(self.details_frame, i+1, item.body, item.info)


    def __change_visibility(self, val):
        if val:
            self.grid(column=0, row=self.row, sticky="NWSE")
        else:
            self.grid_forget()

    
    def __clear(self):
        self.active_category = None     # details_frame будет обновлён здесь
        self.after(0, self.__update_buttons_frame)
import tkinter as tk
from tkinter import ttk, PhotoImage
from pathlib import Path

from context import PluginContext
from settings import poi_categories as CATEGORIES
from .table import Table
from ._dataitem import _DataItem
from modules.debug import debug

import myNotebook as nb

# Подключение функции перевода
import functools
_translate = functools.partial(PluginContext._tr_template, context=__file__)


categories_localized = {
    "Anomaly": _translate("Anomaly"),
    "Biology": _translate("Biology"),
    "Cloud": _translate("Cloud"),
    "Geology": _translate("Geology"),
    "Guardian": _translate("Guardian"),
    "Human": _translate("Human"),
    "Other": _translate("Other"),
    "Planets": _translate("Planets"),
    "Ring": _translate("Ring"),
    "Thargoid": _translate("Thargoid"),
    "Tourist": _translate("Tourist"),
    "None": _translate("None")
}


class _ModuleSettingsGroup(ttk.Frame):
    def __init__(self, parent: tk.Misc, qualname: str, localized_name: str, enabled: bool):
        super().__init__(parent)
        self.__m_localized_name = localized_name
        self.__m_qualname = qualname

        self.__status_var = tk.BooleanVar(value=enabled)
        self.__status_checkbox = nb.Checkbutton(self, variable=self.__status_var)
        self.__status_checkbox.pack(side='left')

        self.__name_label = nb.Label(self, text=self.__m_localized_name, justify='left')
        self.__name_label.pack(side='left')

    def change_state(self, new_state):
        self.__name_label.configure(state=new_state)
        self.__status_checkbox.configure(state=new_state)

    @property
    def enabled(self):
        return self.__status_var.get()

    @property
    def module_qualname(self):
        return self.__m_qualname


class VSettingsFrame(tk.Frame):
    def __init__(self, parent: tk.Misc, row: int, vslz_shown: bool, modules_config: list[tuple[str, str, bool]]):
        super().__init__(parent, bg="white")

        self.module_name_label = nb.Label(self, text=_translate("Visualizer settings:"))
        self.module_name_label.pack(side="top", anchor="w")

        # практически _ModuleSettingsGroup, только для визуализатора целиком
        self.vis_frame = tk.Frame(self, bg="white")
        self.vis_label = nb.Label(self.vis_frame, text=_translate("Show visualizer module:"))
        self.vis_checkbox_var = tk.BooleanVar(self.vis_frame, value=vslz_shown)
        self.vis_checkbox = nb.Checkbutton(self.vis_frame, variable=self.vis_checkbox_var, command=self.change_groups_state)
        self.vis_label.grid(column=0, row=0)
        self.vis_checkbox.grid(column=1, row=0, padx=5)
        self.vis_frame.pack(side='top', fill='x')

        self.delimeter_label = nb.Label(self, text=_translate("Show output from selected modules only:"))
        self.delimeter_label.pack(side='top', anchor='w')

        self.module_frames = [_ModuleSettingsGroup(self, mod, name, enabled) for (mod, name, enabled) in modules_config]
        self.modules_dummy_label = nb.Label(self, text=_translate("[No registered modules found]"))
        if len(self.module_frames) == 0:
            self.modules_dummy_label.pack(side='left', anchor='w')
        else:
            for frame in self.module_frames:
                frame.pack(side='top', anchor='w')

        self.change_groups_state()
        self.grid(column=0, row=row, sticky="NWSE")


    def change_groups_state(self):
        new_state = "normal" if self.vis_checkbox_var.get() is True else "disabled"
        for frame in self.module_frames:
            frame.change_state(new_state)
        self.delimeter_label.configure(state=new_state)
        self.modules_dummy_label.configure(state=new_state)


    def get_current_config(self) -> tuple[bool, dict[str, bool]]:
        vslz_shown = self.vis_checkbox_var.get()
        modules_config = dict()
        for module in self.module_frames:
            modules_config[module.module_qualname] = module.enabled
        return vslz_shown, modules_config



class _IconButton(nb.Button):
    def __init__(self, parent, category, callback):
        super().__init__(parent)
        self.category = category
        self.__callback = callback

        icons_path = Path(PluginContext.plugin_dir, "icons")
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


class VisualizerView(tk.Frame):
    def __init__(self, parent: tk.Misc, row: int):
        self.__active_ctg: str | None = None
        # забудьте, что видели этот атрибут. всё взаимодействие через self.active_category

        super().__init__(parent)
        self.row = row
        self.data: dict[str, set[_DataItem]] = dict()      # с разбивкой по категориям

        # фрейм с кнопками-иконками категорий
        self.buttons_frame = tk.Frame(self)
        self.buttons_dummy_label = tk.Label(self.buttons_frame, text=_translate("Visualizer: No data yet."))
        self.buttons_dummy_label.pack(side='left', fill='x')
        self.buttons: dict[str, _IconButton] = {}
        for ctg in CATEGORIES:
            self.buttons[ctg] = _IconButton(self.buttons_frame, ctg, self.__button_callback)
        self.buttons_frame.pack(side='top', fill='x')

        # фрейм с названием отображаемой категории
        self.category_frame = ttk.Frame(self)       # маппится в ___ при наличии данных к отображению
        self.category_text_label = tk.Label(self.category_frame, text=_translate("Displayed category:"))
        self.category_text_label.pack(side='left')
        self.active_category_var = tk.StringVar(value="")
        self.active_category_label = tk.Label(self.category_frame, textvariable=self.active_category_var)
        self.active_category_label.pack(side='left', padx=3)

        # фрейм с данными по активной категории
        headers = [
            _translate("Body"),
            _translate("POI")
        ]
        self.details_frame = ttk.Frame(self)         # маппится в ___ при наличии данных к отображению
        self.details_table = Table(self.details_frame, headers)
        self.details_table.pack(side="top", fill="x")


    def display(self, data: _DataItem | list[_DataItem]):
        if isinstance(data, _DataItem):
            data = [data,]
        update_buttons = False
        update_content = False
        for item in data:
            ctg = item.category
            if ctg not in self.data:
                self.data[ctg] = set()
                update_buttons = True
            self.data[ctg].add(item)
            if ctg == self.active_category:
                update_content = True
        if update_buttons:
            self.after(0, self.__update_buttons)
        if update_content:
            self.after(0, self.__update_content)


    def clear(self):
        self.data.clear()
        self.active_category = None


    def change_visibility(self, visible: bool):
        self.after(0, self.__change_visibility, visible)
        debug("[VisualizerView] Visibility set to {}.", visible)


    @property
    def active_category(self):
        return self.__active_ctg

    @active_category.setter
    def active_category(self, value: str | None):
        assert value in CATEGORIES or value is None     # TODO: удалить после тестов?
        self.__active_ctg = value
        self.after(0, self.__update_buttons)
        self.after(0, self.__update_content)


    # нижеизложенные методы должны вызываться ИСКЛЮЧИТЕЛЬНО в главном потоке

    def __update_buttons(self):         # noqa: E301
        self.buttons_dummy_label.pack_forget()

        for category, button in self.buttons.items():
            button.deactivate()
            if category not in self.data:
                button.pack_forget()
            else:
                button.pack(side="left")
                if category == self.__active_ctg:
                    button.activate()

        if len(self.data) == 0:
            self.buttons_dummy_label.pack(side="left", fill="x")


    def __update_content(self):
        self.details_table.clear()
        if self.active_category is None:
            self.category_frame.pack_forget()
            self.details_frame.pack_forget()
            return

        self.active_category_var.set(categories_localized[self.active_category])
        data = sorted(self.data[self.active_category])
        for item in data:
            self.details_table.insert(item.body, item.text)
        self.category_frame.pack(side="top", fill="x")
        self.details_frame.pack(side="top", fill="x")


    def __change_visibility(self, visible: bool):
        if not visible:
            self.grid_forget()
        else:
            self.grid(column=0, row=self.row, sticky="NWSE")

    def __button_callback(self, category: str):
        if category == self.active_category:
            self.active_category = None
        else:
            self.active_category = category

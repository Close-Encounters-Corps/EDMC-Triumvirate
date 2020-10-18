import json
import tkinter as tk
import traceback

import myNotebook as nb

from .http import WebClient
from ..debug import Debug, debug, error
from .conf import config
from .module import Module


def _encode(item):
    if isinstance(item, set):
        return list(item)
    raise TypeError(item)

class CecApi(WebClient, Module):
    def __init__(self, base_url):
        super().__init__(base_url)
        self.token = config.get("triumvirate-token")
        self.text = None

    def draw_settings(self, parent_widget, cmdr, is_beta, position):
        nb.Label(parent_widget, text="Токен Triumvirate со страницы сайта").grid(row=10, column=0, sticky="NW")
        self.text = tk.Text(parent_widget, height=1, width=45)
        self.text.grid(row=11, column=0, sticky="NW")
        if isinstance(self.token, str):
            self.text.insert(1.0, self.token)

    def on_settings_changed(self, cmdr, is_beta):
        token = self.text.get(1.0, tk.END).strip()
        self.token = token
        config.set("triumvirate-token", token)

    def submit(self, url, data, method="POST"):
        if not self.token:
            return
        try:
            encoded_json = json.dumps(data, default=_encode)
            self.request(method, url, json=encoded_json, headers={"X-Triumvirate-Token": self.token})
            debug("Sent data to {} successfully.", url)
        except Exception as e:
            error(f"Error submitting data: {e}")
            if Debug.debugswitch == 1:
                traceback.print_exc()

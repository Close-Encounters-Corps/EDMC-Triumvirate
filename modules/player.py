"""
Проигрыватель звуковых файлов.
"""

import os
import sys

from .playsound import playsound
from .lib.thread import Thread


class Player(Thread):
    def __init__(self, plugin_dir, sounds):
        super().__init__()
        self.sounds = sounds
        self.plugin_dir = plugin_dir

    def run(self):
        for soundfile in self.sounds:
            playsound(os.path.join(self.plugin_dir, soundfile))

# -*- coding: utf-8 -*-
from os import path
import sys
# грязный хак чтобы подключить корень проекта в sys.path во время тестов
sys.path.append(path.dirname(path.dirname(__file__)))

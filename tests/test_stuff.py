# -*- coding: utf-8 -*-
import pytest

from modules.lib.cmdr import find_cmdr
from modules.lib.context import Context

def test_find_cmdr():
    assert find_cmdr("Kamish")

def test_context():
    ctx = Context()
    ctx.check = True
    assert "check" in ctx._store
    assert ctx.check == True
    with pytest.raises(AttributeError):
        ctx.nonexistent

# -*- coding: utf-8 -*-
import pytest

# from modules.lib.cmdr import find_cmdr
from modules.lib.context import Context
from modules.lib.version import Version

# def test_find_cmdr():
#     assert find_cmdr("Kamish")
#     assert find_cmdr(":NON:EXISTENT:")

def test_context():
    ctx = Context()
    ctx.check = True
    assert "check" in ctx._store
    assert ctx.check == True
    with pytest.raises(AttributeError):
        ctx.nonexistent


def test_version():
    assert Version("0.1.0") < Version("0.2.0")
    assert Version("0.1.0") == Version("0.1.0")
    assert Version("1.0.1") > Version("0.1.0")
    assert Version("1.0.1") > Version("1.0.0")
    assert Version("1.0.1") < Version("1.1.0.1")
    assert not Version("1.0.1") < Version("1.0.0")
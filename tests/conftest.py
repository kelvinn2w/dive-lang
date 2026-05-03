"""Pytest köməkçi fixture-ları."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

import pytest

from dive.interpreter import Interpreter


@pytest.fixture
def run():
    def _run(source: str, filename: str = "<test>") -> str:
        interp = Interpreter(filename=filename)
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run(source, filename=filename)
        return buf.getvalue()

    return _run


@pytest.fixture
def run_value():
    """Mənbədə son ifadəni qaytarır (statement deyil, dəyər)."""

    def _run(source: str) -> object:
        interp = Interpreter(filename="<test>")
        return interp.run(source, filename="<test>")

    return _run

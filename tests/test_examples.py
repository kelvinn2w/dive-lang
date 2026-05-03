"""Bütün nümunə proqramların xətasız işlədiyini yoxla."""

import io
import os
from contextlib import redirect_stdout

import pytest

from dive.interpreter import Interpreter

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


def _example_files():
    if not os.path.isdir(EXAMPLES_DIR):
        return []
    return sorted(
        os.path.join(EXAMPLES_DIR, name)
        for name in os.listdir(EXAMPLES_DIR)
        if name.endswith(".dive")
    )


@pytest.mark.parametrize("path", _example_files())
def test_example_runs(path):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    interp = Interpreter(filename=path)
    buf = io.StringIO()
    with redirect_stdout(buf):
        interp.run(source, filename=path)
    # Hər nümunə nə isə çıxış verməlidir
    assert buf.getvalue().strip() != ""

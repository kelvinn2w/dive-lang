"""Modul (import) testləri."""

import os
import textwrap


def test_builtin_math(run):
    src = """
import math
print(math.pi > 3 and math.pi < 4)
print(math.sqrt(16))
"""
    assert run(src).split() == ["true", "4.0"]


def test_builtin_random(run):
    src = """
import random
random.seed(0)
v = random.randint(1, 100)
print(v >= 1 and v <= 100)
"""
    assert run(src).strip() == "true"


def test_user_module(tmp_path, run):
    mod = tmp_path / "mymod.dive"
    mod.write_text(textwrap.dedent("""
        function ikiqat(x):
            return x * 2

        SABIT = 42
    """))
    main = tmp_path / "main.dive"
    main.write_text(textwrap.dedent(f'''
        import "{mod}" as m
        print(m.ikiqat(5))
        print(m.SABIT)
    '''))
    src = main.read_text()
    assert run(src, filename=str(main)).split() == ["10", "42"]


def test_module_relative_path(tmp_path, run):
    sub = tmp_path
    helper = sub / "helper.dive"
    helper.write_text("function f(x):\n    return x + 1\n")
    main = sub / "main.dive"
    main.write_text('import "helper.dive" as h\nprint(h.f(10))\n')
    src = main.read_text()
    assert run(src, filename=str(main)).strip() == "11"

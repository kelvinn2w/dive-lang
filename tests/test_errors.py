"""Xəta idarəetmə testləri."""

import pytest

from dive.errors import DiveError, NameDiveError, TypeDiveError


def test_try_catch(run):
    src = """
try:
    throw "xeta"
catch e:
    print("tutdum:", e)
"""
    assert run(src).strip() == "tutdum: xeta"


def test_try_finally(run):
    src = """
try:
    print("try")
finally:
    print("finally")
"""
    assert run(src).strip().split("\n") == ["try", "finally"]


def test_try_catch_finally(run):
    src = """
try:
    throw "x"
catch e:
    print("c:", e)
finally:
    print("f")
"""
    assert run(src).strip().split("\n") == ["c: x", "f"]


def test_runtime_errors_caught(run):
    src = """
try:
    x = 1 / 0
catch e:
    print("tutdum")
"""
    assert run(src).strip() == "tutdum"


def test_undefined_variable(run):
    with pytest.raises(NameDiveError):
        run("print(naməlum_dəyişən)\n")


def test_type_error(run):
    with pytest.raises(TypeDiveError):
        run('print("abc" - 1)\n')


def test_throw_object(run):
    src = """
try:
    throw {"kod": 42, "mesaj": "xəta"}
catch e:
    print(e["kod"])
    print(e["mesaj"])
"""
    assert run(src).strip().split("\n") == ["42", "xəta"]

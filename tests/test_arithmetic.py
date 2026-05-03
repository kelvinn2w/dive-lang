"""Arifmetik və müqayisə testləri."""


def test_basic_arithmetic(run):
    out = run("print(1 + 2 * 3)\nprint(10 / 4)\nprint(10 // 4)\nprint(10 % 3)\n")
    assert out.split() == ["7", "2.5", "2", "1"]


def test_power(run):
    out = run("print(2 ** 10)\nprint(2 ** 3 ** 2)\n")
    assert out.split() == ["1024", "512"]


def test_unary(run):
    out = run("print(-5)\nprint(--5)\nprint(+3)\n")
    assert out.split() == ["-5", "5", "3"]


def test_comparison(run):
    src = "\n".join([
        "print(1 < 2)",
        "print(2 < 1)",
        "print(2 == 2)",
        "print(2 != 3)",
        "print(1 < 2 < 3)",
        "print(1 < 2 > 3)",
    ])
    out = run(src + "\n")
    assert out.split() == ["true", "false", "true", "true", "true", "false"]


def test_logical_short_circuit(run):
    out = run("print(true and 5)\nprint(false or 7)\nprint(not 0)\n")
    assert out.split() == ["5", "7", "true"]


def test_string_concat(run):
    out = run('print("a" + "b" + "c")\n')
    assert out.strip() == "abc"


def test_string_repeat(run):
    out = run('print("ab" * 3)\nprint(3 * "x")\n')
    assert out.strip().split("\n") == ["ababab", "xxx"]


def test_list_concat_repeat(run):
    out = run('print([1,2] + [3,4])\nprint([0] * 3)\n')
    assert out.strip().split("\n") == ["[1, 2, 3, 4]", "[0, 0, 0]"]


def test_division_by_zero(run):
    import pytest
    from dive.errors import ValueDiveError, DiveError
    with pytest.raises(DiveError):
        run("print(1 / 0)\n")

"""Funksiya testləri."""


def test_simple_function(run):
    src = """
function add(a, b):
    return a + b
print(add(2, 3))
"""
    assert run(src).strip() == "5"


def test_default_args(run):
    src = """
function greet(ad, sözü="Salam"):
    return sözü + ", " + ad
print(greet("Elvin"))
print(greet("Aysel", sözü="Hi"))
"""
    assert run(src).strip().split("\n") == ["Salam, Elvin", "Hi, Aysel"]


def test_recursion(run):
    src = """
function fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)
print(fib(10))
"""
    assert run(src).strip() == "55"


def test_closure(run):
    src = """
function make_adder(x):
    function add(y):
        return x + y
    return add

add5 = make_adder(5)
print(add5(3))
print(add5(10))
"""
    assert run(src).split() == ["8", "15"]


def test_lambda(run):
    src = """
sq = lambda x: x * x
print(sq(7))
add = lambda a, b: a + b
print(add(2, 3))
"""
    assert run(src).split() == ["49", "5"]


def test_higher_order(run):
    src = """
function apply(fn, x):
    return fn(x)
print(apply(lambda v: v + 1, 41))
"""
    assert run(src).strip() == "42"


def test_function_too_many_args(run):
    import pytest
    from dive.errors import DiveError
    src = """
function f(a):
    return a
print(f(1, 2))
"""
    with pytest.raises(DiveError):
        run(src)


def test_function_missing_arg(run):
    import pytest
    from dive.errors import DiveError
    src = """
function f(a, b):
    return a + b
print(f(1))
"""
    with pytest.raises(DiveError):
        run(src)

"""Şərt və döngü testləri."""


def test_if_elif_else(run):
    src = """
function k(x):
    if x < 0:
        return "mənfi"
    elif x == 0:
        return "sıfır"
    else:
        return "müsbət"

print(k(-3))
print(k(0))
print(k(7))
"""
    assert run(src).split() == ["mənfi", "sıfır", "müsbət"]


def test_while_break(run):
    src = """
i = 0
while true:
    if i >= 5:
        break
    print(i)
    i += 1
"""
    assert run(src).split() == ["0", "1", "2", "3", "4"]


def test_for_continue(run):
    src = """
for i in range(0, 10):
    if i % 2 == 0:
        continue
    print(i)
"""
    assert run(src).split() == ["1", "3", "5", "7", "9"]


def test_nested_loops(run):
    src = """
for i in range(0, 3):
    for j in range(0, 3):
        if j == 2:
            break
        print(i, j)
"""
    expected = "0 0\n0 1\n1 0\n1 1\n2 0\n2 1\n"
    assert run(src) == expected


def test_for_over_string(run):
    src = """
for ch in "abc":
    print(ch)
"""
    assert run(src).split() == ["a", "b", "c"]


def test_for_over_dict(run):
    src = """
d = {"a": 1, "b": 2}
keys = []
for k in d:
    keys.append(k)
print(sorted(keys))
"""
    assert run(src).strip() == '["a", "b"]'

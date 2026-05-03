"""Siyahı və lüğət testləri."""


def test_list_basics(run):
    src = """
xs = [1, 2, 3, 4]
print(len(xs))
print(xs[0])
print(xs[-1])
print(xs[1:3])
"""
    assert run(src).strip().split("\n") == ["4", "1", "4", "[2, 3]"]


def test_list_methods(run):
    src = """
xs = [3, 1, 2]
xs.sort()
print(xs)
xs.reverse()
print(xs)
xs.append(4)
print(xs)
xs.remove(1)
print(xs)
"""
    assert run(src).strip().split("\n") == [
        "[1, 2, 3]",
        "[3, 2, 1]",
        "[3, 2, 1, 4]",
        "[3, 2, 4]",
    ]


def test_dict_basics(run):
    src = """
d = {"a": 1, "b": 2}
print(d["a"])
d["c"] = 3
print(d.get("c"))
print(d.has("b"))
print(d.has("z"))
"""
    assert run(src).split() == ["1", "3", "true", "false"]


def test_dict_iteration(run):
    src = """
d = {"a": 1, "b": 2}
items = []
for k in d:
    items.append(k + "=" + str(d[k]))
print(sorted(items))
"""
    assert run(src).strip() == '["a=1", "b=2"]'


def test_string_methods(run):
    src = """
s = "Salam, Dive"
print(s.upper())
print(s.lower())
print(s.replace("Dive", "Elvin"))
print(s.split(", "))
print("-".join(["a", "b", "c"]))
print(s.length())
"""
    assert run(src).strip().split("\n") == [
        "SALAM, DIVE",
        "salam, dive",
        "Salam, Elvin",
        '["Salam", "Dive"]',
        "a-b-c",
        "11",
    ]


def test_in_operator(run):
    src = """
print(2 in [1, 2, 3])
print(5 in [1, 2, 3])
print("a" in "salam")
print("z" in "salam")
print("k" in {"k": 1})
"""
    assert run(src).split() == ["true", "false", "true", "false", "true"]

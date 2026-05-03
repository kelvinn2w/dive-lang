"""Sinif (class) testləri."""


def test_basic_class(run):
    src = """
class Point:
    function init(self, x, y):
        self.x = x
        self.y = y

    function uzaqliq(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

p = Point(3, 4)
print(p.x)
print(p.y)
print(p.uzaqliq())
"""
    assert run(src).split() == ["3", "4", "5.0"]


def test_inheritance(run):
    src = """
class A:
    function init(self, n):
        self.n = n
    function de(self):
        return "A:" + str(self.n)

class B(A):
    function de(self):
        return "B:" + str(self.n)

a = A(1)
b = B(2)
print(a.de())
print(b.de())
"""
    assert run(src).split() == ["A:1", "B:2"]


def test_inheritance_method_inherited(run):
    src = """
class A:
    function init(self):
        self.x = 10
    function geri(self):
        return self.x

class B(A):
    pass

b = B()
print(b.geri())
"""
    assert run(src).strip() == "10"


def test_isinstance(run):
    src = """
class A:
    pass

class B(A):
    pass

a = A()
b = B()
print(isinstance(a, A))
print(isinstance(b, A))
print(isinstance(a, B))
"""
    assert run(src).split() == ["true", "true", "false"]


def test_tostring_method(run):
    src = """
class P:
    function init(self, n):
        self.n = n
    function tostring(self):
        return "P[" + str(self.n) + "]"

p = P(7)
print(p)
print(str(p))
"""
    assert run(src).split() == ["P[7]", "P[7]"]

# Dive — a simple programming language

**Dive** is a Python-like, indentation-based, easy-to-use programming language
that lets you do almost anything. The interpreter is written in Python, so it
runs anywhere Python runs.

```text
function greet(name):
    print("Hello, " + name + "!")

greet("World")
```

## Why Dive?

- **Simple syntax** — Python-like, readable, intuitive
- **Full-featured** — classes, modules, file I/O, exceptions
- **English keywords** — `if`, `while`, `function`, `class`, `import`
- **Zero dependencies** — only requires Python 3.9+
- **Extensible** — easy to add new built-in functions

## Installation

```bash
git clone https://github.com/kelvinn2w/dive-lang.git
cd dive-lang
pip install -e .
```

Verify:

```bash
dive --version
dive examples/01_hello.dive
```

REPL is also available:

```bash
dive        # interactive mode
```

## Quick tour

### Hello World

```text
print("Hello, World!")
```

### Variables and types

```text
name = "Elvin"          # string
age = 25                # int
height = 1.78           # float
is_developer = true     # bool
nothing = none          # null

print(type(age))        # int
print(type(name))       # string
```

### Conditionals

```text
if age < 18:
    print("child")
elif age < 65:
    print("adult")
else:
    print("senior")
```

### Loops

```text
for i in range(0, 5):
    print(i)

i = 0
while i < 3:
    print(i)
    i += 1

# break and continue work too
for n in range(0, 10):
    if n % 2 == 0:
        continue
    if n > 5:
        break
    print(n)
```

### Functions

```text
function power(base, exp=2):
    return base ** exp

print(power(3))          # 9
print(power(2, 10))      # 1024

# Lambdas
double = lambda x: x * 2
print(double(7))         # 14

# Closures
function counter(start=0):
    n = [start]
    function next_value():
        n[0] = n[0] + 1
        return n[0]
    return next_value

c = counter(10)
print(c())  # 11
print(c())  # 12
```

### Classes and inheritance

```text
class Animal:
    function init(self, name):
        self.name = name
    function sound(self):
        return "..."
    function introduce(self):
        print(self.name + " says: " + self.sound())

class Dog(Animal):
    function sound(self):
        return "Woof!"

Dog("Rex").introduce()  # Rex says: Woof!
```

`init` is the constructor (same as Python's `__init__`). If a `tostring` method
is defined, `print(obj)` and `str(obj)` will call it.

### Lists

```text
xs = [1, 2, 3, 4]
xs.append(5)
print(xs)              # [1, 2, 3, 4, 5]
print(xs[1:3])         # [2, 3]
print(xs[::-1])        # [5, 4, 3, 2, 1]
print(len(xs))         # 5

# methods: append, pop, insert, remove, index, count,
# sort, reverse, clear, copy, extend, join, length
```

### Dicts

```text
d = {"name": "Elvin", "age": 25}
d["city"] = "Baku"

print(d["name"])
print(d.keys())
print(d.values())
print(d.has("age"))    # true

for k in d:
    print(k + " -> " + str(d[k]))
```

### Errors (try/catch/finally)

```text
function divide(a, b):
    if b == 0:
        throw "Division by zero is not allowed!"
    return a / b

try:
    print(divide(10, 0))
catch err:
    print("Error:", err)
finally:
    print("Done")
```

`throw` can throw any value (string, dict, class instance, etc.).

### Modules

Two flavours of import:

```text
import math                  # built-in module
import "utils.dive" as u     # your own files (by path)

print(math.sqrt(16))
print(u.double(21))
```

#### Built-in modules
- `math` — pi, e, tau, sqrt, pow, log, log2, log10, exp, sin, cos, tan,
  asin, acos, atan, atan2, floor, ceil, round, gcd, factorial
- `random` — seed, random, randint, choice, shuffle, uniform
- `time` — now, sleep, format
- `os` — getenv, setenv, listdir, exists, cwd, join

### File I/O

```text
write_file("notes.txt", "Hello!\n")
content = read_file("notes.txt")
print(content)

f = open("notes.txt", "a")
f.writeline("a new line")
f.close()
```

### String methods

`s.upper()`, `s.lower()`, `s.strip()`, `s.lstrip()`, `s.rstrip()`,
`s.split(sep?)`, `s.join(items)`, `s.replace(a, b)`, `s.startswith(s)`,
`s.endswith(s)`, `s.contains(s)`, `s.find(s)`, `s.count(s)`, `s.length()`,
`s.format(*args)`.

## Built-in functions

`print`, `input`, `len`, `range`, `str`, `int`, `float`, `bool`, `list`, `dict`,
`abs`, `min`, `max`, `sum`, `sorted`, `reversed`, `type`, `isinstance`, `repr`,
`open`, `read_file`, `write_file`, `append_file`, `file_exists`.

## Keywords

```
if elif else while for in function return class import as from
true false none and or not try catch finally throw
break continue pass lambda
```

## CLI

```bash
dive FILE.dive          # run a file
dive -c "print(1+2)"    # run code directly
dive                    # REPL
dive --version
```

## Project layout

```
dive-lang/
├── dive/
│   ├── __init__.py
│   ├── __main__.py        # CLI
│   ├── lexer.py           # tokenizer
│   ├── parser.py          # recursive descent parser
│   ├── ast_nodes.py       # AST node types
│   ├── interpreter.py     # tree-walking interpreter
│   ├── environment.py     # scope / variables
│   ├── values.py          # DiveFunction, DiveClass, DiveInstance
│   ├── builtins.py        # built-in functions and modules
│   └── errors.py          # error classes
├── examples/              # example programs
├── tests/                 # pytest test suite
├── pyproject.toml
└── README.md
```

## Tests

```bash
pip install -e ".[dev]"
pytest -q
```

## Extending

To add a new built-in function, edit `dive/builtins.py`, add the function and
register it inside `install_builtins`.

For new operators you'll need matching changes in the lexer, parser and
interpreter.

## License

MIT

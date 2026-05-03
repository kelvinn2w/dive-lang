# Dive — sadə proqramlaşdırma dili

**Dive** — Python-bənzər, girinti əsaslı, hər şeyi etməyə imkan verən sadə bir
proqramlaşdırma dilidir. İnterpretator Python ilə yazılıb, ona görə də hər
yerdə işləyir.

```text
function salamla(ad):
    print("Salam, " + ad + "!")

salamla("Dünya")
```

## Niyə Dive?

- **Sadə sintaksis** — Python-a oxşar, oxunaqlı, başa düşülən
- **Hər şeyi etməyə imkan verir** — siniflər, modullar, fayl I/O, exceptions
- **İngiliscə açar sözlər** — `if`, `while`, `function`, `class`, `import`
- **Sıfır asılılıq** — yalnız Python 3.9+ tələb olunur
- **Genişlənə bilən** — yeni built-in funksiya əlavə etmək asandır

## Quraşdırma

```bash
git clone https://github.com/kelvinn2w/dive-lang.git
cd dive-lang
pip install -e .
```

Yoxla:

```bash
dive --version
dive examples/01_hello.dive
```

REPL də var:

```bash
dive        # interaktiv rejim
```

## Tez baxış

### Salam Dünya

```text
print("Salam, Dünya!")
```

### Dəyişənlər və tiplər

```text
ad = "Elvin"            # string
yas = 25                # int
boy = 1.78              # float
proqramcidir = true     # bool
hicnese = none          # null

print(type(yas))        # int
print(type(ad))         # string
```

### Şərtlər

```text
if yas < 18:
    print("uşaq")
elif yas < 65:
    print("böyük")
else:
    print("yaşlı")
```

### Döngülər

```text
for i in range(0, 5):
    print(i)

i = 0
while i < 3:
    print(i)
    i += 1

# break və continue də işləyir
for n in range(0, 10):
    if n % 2 == 0:
        continue
    if n > 5:
        break
    print(n)
```

### Funksiyalar

```text
function quvvet(taban, ust=2):
    return taban ** ust

print(quvvet(3))         # 9
print(quvvet(2, 10))     # 1024

# Lambda
ikiqat = lambda x: x * 2
print(ikiqat(7))         # 14

# Closures
function sayğac(başlanğıc=0):
    n = [başlanğıc]
    function növbəti():
        n[0] = n[0] + 1
        return n[0]
    return növbəti

c = sayğac(10)
print(c())  # 11
print(c())  # 12
```

### Siniflər və irsiyyət

```text
class Heyvan:
    function init(self, ad):
        self.ad = ad
    function ses(self):
        return "..."
    function tanit(self):
        print(self.ad + " deyir: " + self.ses())

class It(Heyvan):
    function ses(self):
        return "Hav-hav!"

It("Rex").tanit()       # Rex deyir: Hav-hav!
```

`init` — konstruktordur (Python-da `__init__` ilə eyni). `tostring` metodu varsa,
`print(obyekt)` və `str(obyekt)` onu çağırır.

### Siyahılar

```text
xs = [1, 2, 3, 4]
xs.append(5)
print(xs)              # [1, 2, 3, 4, 5]
print(xs[1:3])         # [2, 3]
print(xs[::-1])        # [5, 4, 3, 2, 1]
print(len(xs))         # 5

# metodlar: append, pop, insert, remove, index, count,
# sort, reverse, clear, copy, extend, join, length
```

### Lüğətlər

```text
d = {"ad": "Elvin", "yas": 25}
d["sehr"] = "Bakı"

print(d["ad"])
print(d.keys())
print(d.values())
print(d.has("yas"))     # true

for k in d:
    print(k + " -> " + str(d[k]))
```

### Xətalar (try/catch/finally)

```text
function bol(a, b):
    if b == 0:
        throw "Sıfıra bölmə qadağandır!"
    return a / b

try:
    print(bol(10, 0))
catch err:
    print("Xəta:", err)
finally:
    print("Tamamlandı")
```

`throw` istənilən dəyəri ata bilər (string, dict, sinif obyekti və s.).

### Modullar

İki cür import:

```text
import math                  # built-in modul
import "utils.dive" as u     # öz fayllarınız (yola görə)

print(math.sqrt(16))
print(u.ikiqat(21))
```

#### Daxili modullar
- `math` — pi, e, tau, sqrt, pow, log, log2, log10, exp, sin, cos, tan,
  asin, acos, atan, atan2, floor, ceil, round, gcd, factorial
- `random` — seed, random, randint, choice, shuffle, uniform
- `time` — now, sleep, format
- `os` — getenv, setenv, listdir, exists, cwd, join

### Fayl I/O

```text
write_file("notlar.txt", "Salam!\n")
məzmun = read_file("notlar.txt")
print(məzmun)

f = open("notlar.txt", "a")
f.writeline("yeni sətir")
f.close()
```

### String metodları

`s.upper()`, `s.lower()`, `s.strip()`, `s.lstrip()`, `s.rstrip()`,
`s.split(sep?)`, `s.join(items)`, `s.replace(a, b)`, `s.startswith(s)`,
`s.endswith(s)`, `s.contains(s)`, `s.find(s)`, `s.count(s)`, `s.length()`,
`s.format(*args)`.

## Daxili funksiyalar

`print`, `input`, `len`, `range`, `str`, `int`, `float`, `bool`, `list`, `dict`,
`abs`, `min`, `max`, `sum`, `sorted`, `reversed`, `type`, `isinstance`, `repr`,
`open`, `read_file`, `write_file`, `append_file`, `file_exists`.

## Açar sözlər

```
if elif else while for in function return class import as from
true false none and or not try catch finally throw
break continue pass lambda
```

## CLI

```bash
dive FAYL.dive          # faylı icra et
dive -c "print(1+2)"    # birbaşa kod
dive                    # REPL
dive --version
```

## Layihə strukturu

```
dive-lang/
├── dive/
│   ├── __init__.py
│   ├── __main__.py        # CLI
│   ├── lexer.py           # tokenizer
│   ├── parser.py          # recursive descent parser
│   ├── ast_nodes.py       # AST tipləri
│   ├── interpreter.py     # tree-walking interpreter
│   ├── environment.py     # scope/dəyişənlər
│   ├── values.py          # DiveFunction, DiveClass, DiveInstance
│   ├── builtins.py        # daxili funksiya və modullar
│   └── errors.py          # xəta sinifləri
├── examples/              # nümunə proqramlar
├── tests/                 # pytest test suite
├── pyproject.toml
└── README.md
```

## Test

```bash
pip install -e ".[dev]"
pytest -q
```

## Genişləndirmək

Yeni built-in funksiya əlavə etmək üçün `dive/builtins.py` faylına gedib
funksiyanı yazın və `install_builtins` daxilində qeyd edin.

Yeni operatorlar üçün lexer, parser və interpreter-də müvafiq düzəlişlər lazımdır.

## Lisenziya

MIT

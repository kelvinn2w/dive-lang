"""Dive dilinin daxili (built-in) funksiyaları və modulları."""

from __future__ import annotations

import math
import os
import random
import time
from typing import Dict, List, Optional

from .environment import Environment
from .errors import (
    IndexDiveError,
    RuntimeDiveError,
    TypeDiveError,
    ValueDiveError,
)
from .values import DiveClass, DiveInstance, DiveModule, BuiltinFunction


def _to_str(value: object) -> str:
    """Dive üçün stringləşdirmə (Python repr-dən fərqli)."""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "none"
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "[" + ", ".join(_to_repr(v) for v in value) + "]"
    if isinstance(value, dict):
        items = ", ".join(f"{_to_repr(k)}: {_to_repr(v)}" for k, v in value.items())
        return "{" + items + "}"
    if isinstance(value, DiveInstance):
        # __str__ ekvivalentini yoxla: `tostring` metodu varsa onu çağır
        method = value.klass.find_method("tostring")
        if method is not None:
            from .interpreter import _GLOBAL_INTERPRETER
            interp = _GLOBAL_INTERPRETER.get()
            if interp is not None:
                result = method.bind(value).call(interp, [], {})
                return _to_str(result)
        return f"<{value.klass.name} obyekti>"
    return str(value)


def _to_repr(value: object) -> str:
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return _to_str(value)


def _check_args(name: str, args: list, expected: int) -> None:
    if len(args) != expected:
        raise TypeDiveError(
            f"'{name}' {expected} arqument gözləyir, {len(args)} verildi"
        )


# --------- əsas funksiyalar ---------


def b_print(*args: object, sep: str = " ", end: str = "\n") -> None:
    text = sep.join(_to_str(a) for a in args)
    print(text, end=end)


def b_input(prompt: str = "") -> str:
    return input(_to_str(prompt))


def b_len(value: object) -> int:
    if isinstance(value, (str, list, dict)):
        return len(value)
    raise TypeDiveError(f"'len' bu tipə tətbiq olunmur: {_type_name(value)}")


def b_range(*args: object) -> list:
    if len(args) == 1:
        start, stop, step = 0, args[0], 1
    elif len(args) == 2:
        start, stop, step = args[0], args[1], 1
    elif len(args) == 3:
        start, stop, step = args
    else:
        raise TypeDiveError("'range' 1-3 arqument gözləyir")
    if not all(isinstance(x, int) for x in (start, stop, step)):
        raise TypeDiveError("'range' yalnız tam ədədlərlə işləyir")
    if step == 0:
        raise ValueDiveError("'range' addımı 0 ola bilməz")
    return list(range(start, stop, step))


def b_str(value: object = "") -> str:
    return _to_str(value)


def b_int(value: object = 0, base: int = 10) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip(), base)
        except ValueError:
            raise ValueDiveError(f"'{value}' tam ədədə çevrilə bilmir")
    raise TypeDiveError(f"'int' bu tipi qəbul etmir: {_type_name(value)}")


def b_float(value: object = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            raise ValueDiveError(f"'{value}' kəsr ədədə çevrilə bilmir")
    raise TypeDiveError(f"'float' bu tipi qəbul etmir: {_type_name(value)}")


def b_bool(value: object = False) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return len(value) > 0
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def b_list(value: object = ()) -> list:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, str):
        return list(value)
    if isinstance(value, dict):
        return list(value.keys())
    if value == ():
        return []
    raise TypeDiveError(f"'list' bu tipi qəbul etmir: {_type_name(value)}")


def b_dict(*args: object) -> dict:
    if not args:
        return {}
    if len(args) == 1 and isinstance(args[0], list):
        out: dict = {}
        for item in args[0]:
            if not isinstance(item, list) or len(item) != 2:
                raise TypeDiveError("'dict' (key, value) cütlərindən ibarət siyahı gözləyir")
            out[item[0]] = item[1]
        return out
    raise TypeDiveError("'dict' yalnız boş və ya cütlər siyahısı qəbul edir")


def b_abs(x: object) -> object:
    if isinstance(x, (int, float)):
        return abs(x)
    raise TypeDiveError(f"'abs' bu tipə tətbiq olunmur: {_type_name(x)}")


def b_min(*args: object) -> object:
    if len(args) == 1 and isinstance(args[0], list):
        if not args[0]:
            raise ValueDiveError("'min' boş siyahıya tətbiq oluna bilməz")
        return min(args[0])
    if not args:
        raise TypeDiveError("'min' ən azı 1 arqument gözləyir")
    return min(args)


def b_max(*args: object) -> object:
    if len(args) == 1 and isinstance(args[0], list):
        if not args[0]:
            raise ValueDiveError("'max' boş siyahıya tətbiq oluna bilməz")
        return max(args[0])
    if not args:
        raise TypeDiveError("'max' ən azı 1 arqument gözləyir")
    return max(args)


def b_sum(items: object, start: object = 0) -> object:
    if not isinstance(items, list):
        raise TypeDiveError("'sum' siyahı gözləyir")
    return sum(items, start)


def b_sorted(items: object, reverse: bool = False) -> list:
    if isinstance(items, list):
        return sorted(items, reverse=bool(reverse))
    raise TypeDiveError("'sorted' siyahı gözləyir")


def b_reversed(items: object) -> list:
    if isinstance(items, list):
        return list(reversed(items))
    if isinstance(items, str):
        return list(reversed(items))
    raise TypeDiveError("'reversed' siyahı və ya string gözləyir")


def _type_name(value: object) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, DiveClass):
        return "class"
    if isinstance(value, DiveInstance):
        return value.klass.name
    if isinstance(value, BuiltinFunction):
        return "builtin"
    if isinstance(value, DiveModule):
        return "module"
    return type(value).__name__


def b_type(value: object) -> str:
    return _type_name(value)


def b_isinstance(value: object, klass: object) -> bool:
    if isinstance(klass, DiveClass):
        if isinstance(value, DiveInstance):
            k: Optional[DiveClass] = value.klass
            while k is not None:
                if k is klass:
                    return True
                # Birinci base-i izlə
                if k.bases:
                    k = k.bases[0]
                else:
                    k = None
            return False
        return False
    if isinstance(klass, str):
        return _type_name(value) == klass
    raise TypeDiveError("'isinstance' ikinci arqument sinif və ya string olmalıdır")


def b_repr(value: object) -> str:
    return _to_repr(value)


# --------- fayl I/O ---------


class DiveFile:
    def __init__(self, path: str, mode: str = "r", encoding: str = "utf-8") -> None:
        self.path = path
        self.mode = mode
        try:
            self._fp = open(path, mode, encoding=encoding if "b" not in mode else None)
        except OSError as e:
            raise RuntimeDiveError(f"Fayl açıla bilmədi ({path}): {e}")

    def read(self, size: int = -1) -> str:
        return self._fp.read(size)

    def readline(self) -> str:
        return self._fp.readline()

    def readlines(self) -> list:
        return list(self._fp.readlines())

    def write(self, text: str) -> int:
        return self._fp.write(_to_str(text))

    def writeline(self, text: str) -> int:
        return self._fp.write(_to_str(text) + "\n")

    def close(self) -> None:
        self._fp.close()

    def flush(self) -> None:
        self._fp.flush()

    def __repr__(self) -> str:
        return f"<fayl '{self.path}' mode={self.mode}>"


def b_open(path: str, mode: str = "r", encoding: str = "utf-8") -> DiveFile:
    return DiveFile(path, mode=mode, encoding=encoding)


def b_read_file(path: str, encoding: str = "utf-8") -> str:
    with open(path, "r", encoding=encoding) as f:
        return f.read()


def b_write_file(path: str, content: str, encoding: str = "utf-8") -> int:
    with open(path, "w", encoding=encoding) as f:
        return f.write(_to_str(content))


def b_append_file(path: str, content: str, encoding: str = "utf-8") -> int:
    with open(path, "a", encoding=encoding) as f:
        return f.write(_to_str(content))


def b_file_exists(path: str) -> bool:
    return os.path.exists(path)


# --------- modul: math ---------


def make_math_module() -> DiveModule:
    env = Environment()
    env.define("pi", math.pi)
    env.define("e", math.e)
    env.define("tau", math.tau)
    env.define("inf", math.inf)
    env.define("nan", math.nan)

    def _wrap(name: str, fn, arity=None):
        env.define(name, BuiltinFunction(name=f"math.{name}", func=fn, arity=arity))

    _wrap("sqrt", math.sqrt, 1)
    _wrap("pow", math.pow, 2)
    _wrap("log", math.log, 1)
    _wrap("log2", math.log2, 1)
    _wrap("log10", math.log10, 1)
    _wrap("exp", math.exp, 1)
    _wrap("sin", math.sin, 1)
    _wrap("cos", math.cos, 1)
    _wrap("tan", math.tan, 1)
    _wrap("asin", math.asin, 1)
    _wrap("acos", math.acos, 1)
    _wrap("atan", math.atan, 1)
    _wrap("atan2", math.atan2, 2)
    _wrap("floor", math.floor, 1)
    _wrap("ceil", math.ceil, 1)
    _wrap("round", round, None)
    _wrap("gcd", math.gcd, 2)
    _wrap("factorial", math.factorial, 1)
    return DiveModule("math", env)


# --------- modul: random ---------


def make_random_module() -> DiveModule:
    env = Environment()

    def _seed(s: object = None) -> None:
        random.seed(s)

    def _random_() -> float:
        return random.random()

    def _randint(a: int, b: int) -> int:
        return random.randint(a, b)

    def _choice(items: list) -> object:
        if not isinstance(items, list) or not items:
            raise ValueDiveError("'random.choice' boş olmayan siyahı gözləyir")
        return random.choice(items)

    def _shuffle(items: list) -> list:
        if not isinstance(items, list):
            raise TypeDiveError("'random.shuffle' siyahı gözləyir")
        out = list(items)
        random.shuffle(out)
        return out

    def _uniform(a: float, b: float) -> float:
        return random.uniform(a, b)

    env.define("seed", BuiltinFunction("random.seed", _seed))
    env.define("random", BuiltinFunction("random.random", _random_, 0))
    env.define("randint", BuiltinFunction("random.randint", _randint, 2))
    env.define("choice", BuiltinFunction("random.choice", _choice, 1))
    env.define("shuffle", BuiltinFunction("random.shuffle", _shuffle, 1))
    env.define("uniform", BuiltinFunction("random.uniform", _uniform, 2))
    return DiveModule("random", env)


# --------- modul: time ---------


def make_time_module() -> DiveModule:
    env = Environment()

    def _now() -> float:
        return time.time()

    def _sleep(seconds: float) -> None:
        time.sleep(seconds)

    def _format(seconds: float, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        return time.strftime(fmt, time.localtime(seconds))

    env.define("now", BuiltinFunction("time.now", _now, 0))
    env.define("sleep", BuiltinFunction("time.sleep", _sleep, 1))
    env.define("format", BuiltinFunction("time.format", _format))
    return DiveModule("time", env)


# --------- modul: os ---------


def make_os_module() -> DiveModule:
    env = Environment()

    def _getenv(name: str, default: object = None) -> object:
        return os.environ.get(name, default)

    def _setenv(name: str, value: str) -> None:
        os.environ[name] = _to_str(value)

    def _listdir(path: str = ".") -> list:
        return list(os.listdir(path))

    def _exists(path: str) -> bool:
        return os.path.exists(path)

    def _cwd() -> str:
        return os.getcwd()

    def _join(*parts: str) -> str:
        return os.path.join(*[_to_str(p) for p in parts])

    env.define("getenv", BuiltinFunction("os.getenv", _getenv))
    env.define("setenv", BuiltinFunction("os.setenv", _setenv, 2))
    env.define("listdir", BuiltinFunction("os.listdir", _listdir))
    env.define("exists", BuiltinFunction("os.exists", _exists, 1))
    env.define("cwd", BuiltinFunction("os.cwd", _cwd, 0))
    env.define("join", BuiltinFunction("os.join", _join))
    return DiveModule("os", env)


# --------- string built-in metodları ---------


def string_method(name: str, value: str) -> Optional[BuiltinFunction]:
    methods = {
        "upper": lambda: value.upper(),
        "lower": lambda: value.lower(),
        "strip": lambda: value.strip(),
        "lstrip": lambda: value.lstrip(),
        "rstrip": lambda: value.rstrip(),
        "split": lambda sep=None: value.split(sep) if sep is not None else value.split(),
        "join": lambda items: value.join(_to_str(i) for i in items),
        "replace": lambda a, b: value.replace(_to_str(a), _to_str(b)),
        "startswith": lambda s: value.startswith(_to_str(s)),
        "endswith": lambda s: value.endswith(_to_str(s)),
        "contains": lambda s: _to_str(s) in value,
        "find": lambda s: value.find(_to_str(s)),
        "count": lambda s: value.count(_to_str(s)),
        "length": lambda: len(value),
        "format": _make_string_format(value),
    }
    if name in methods:
        return BuiltinFunction(f"string.{name}", methods[name])
    return None


def _make_string_format(value: str):
    def _format(*args, **kwargs):
        try:
            return value.format(*args, **kwargs)
        except (IndexError, KeyError) as e:
            raise ValueDiveError(f"format xətası: {e}")

    return _format


# --------- list built-in metodları ---------


def list_method(name: str, value: list) -> Optional[BuiltinFunction]:
    def _append(item: object) -> None:
        value.append(item)

    def _pop(index: int = -1) -> object:
        if not value:
            raise IndexDiveError("Boş siyahıdan pop edilə bilməz")
        return value.pop(index)

    def _insert(index: int, item: object) -> None:
        value.insert(index, item)

    def _remove(item: object) -> None:
        try:
            value.remove(item)
        except ValueError:
            raise ValueDiveError(f"Siyahıda '{_to_repr(item)}' yoxdur")

    def _index(item: object) -> int:
        try:
            return value.index(item)
        except ValueError:
            raise ValueDiveError(f"Siyahıda '{_to_repr(item)}' yoxdur")

    def _count(item: object) -> int:
        return value.count(item)

    def _sort(reverse: bool = False) -> None:
        value.sort(reverse=bool(reverse))

    def _reverse() -> None:
        value.reverse()

    def _clear() -> None:
        value.clear()

    def _copy() -> list:
        return list(value)

    def _extend(other: object) -> None:
        if not isinstance(other, list):
            raise TypeDiveError("'extend' siyahı gözləyir")
        value.extend(other)

    def _join(sep: str = "") -> str:
        return _to_str(sep).join(_to_str(v) for v in value)

    def _length() -> int:
        return len(value)

    methods = {
        "append": _append,
        "pop": _pop,
        "insert": _insert,
        "remove": _remove,
        "index": _index,
        "count": _count,
        "sort": _sort,
        "reverse": _reverse,
        "clear": _clear,
        "copy": _copy,
        "extend": _extend,
        "join": _join,
        "length": _length,
    }
    if name in methods:
        return BuiltinFunction(f"list.{name}", methods[name])
    return None


# --------- dict built-in metodları ---------


def dict_method(name: str, value: dict) -> Optional[BuiltinFunction]:
    def _get(key: object, default: object = None) -> object:
        return value.get(key, default)

    def _set(key: object, val: object) -> None:
        value[key] = val

    def _has(key: object) -> bool:
        return key in value

    def _remove(key: object) -> object:
        if key not in value:
            raise ValueDiveError(f"Açar tapılmadı: {_to_repr(key)}")
        return value.pop(key)

    def _keys() -> list:
        return list(value.keys())

    def _values() -> list:
        return list(value.values())

    def _items() -> list:
        return [list(p) for p in value.items()]

    def _length() -> int:
        return len(value)

    def _clear() -> None:
        value.clear()

    def _copy() -> dict:
        return dict(value)

    methods = {
        "get": _get,
        "set": _set,
        "has": _has,
        "remove": _remove,
        "keys": _keys,
        "values": _values,
        "items": _items,
        "length": _length,
        "clear": _clear,
        "copy": _copy,
    }
    if name in methods:
        return BuiltinFunction(f"dict.{name}", methods[name])
    return None


# --------- file built-in metodları ---------


def file_method(name: str, value: DiveFile) -> Optional[BuiltinFunction]:
    methods = {
        "read": value.read,
        "readline": value.readline,
        "readlines": value.readlines,
        "write": value.write,
        "writeline": value.writeline,
        "close": value.close,
        "flush": value.flush,
    }
    if name in methods:
        return BuiltinFunction(f"file.{name}", methods[name])
    return None


# --------- qlobal ad sahəsini doldurmaq ---------


def install_builtins(env: Environment) -> None:
    builtins: Dict[str, BuiltinFunction] = {
        "print": BuiltinFunction("print", b_print),
        "input": BuiltinFunction("input", b_input),
        "len": BuiltinFunction("len", b_len, 1),
        "range": BuiltinFunction("range", b_range),
        "str": BuiltinFunction("str", b_str),
        "int": BuiltinFunction("int", b_int),
        "float": BuiltinFunction("float", b_float),
        "bool": BuiltinFunction("bool", b_bool),
        "list": BuiltinFunction("list", b_list),
        "dict": BuiltinFunction("dict", b_dict),
        "abs": BuiltinFunction("abs", b_abs, 1),
        "min": BuiltinFunction("min", b_min),
        "max": BuiltinFunction("max", b_max),
        "sum": BuiltinFunction("sum", b_sum),
        "sorted": BuiltinFunction("sorted", b_sorted),
        "reversed": BuiltinFunction("reversed", b_reversed),
        "type": BuiltinFunction("type", b_type, 1),
        "isinstance": BuiltinFunction("isinstance", b_isinstance, 2),
        "repr": BuiltinFunction("repr", b_repr, 1),
        "open": BuiltinFunction("open", b_open),
        "read_file": BuiltinFunction("read_file", b_read_file),
        "write_file": BuiltinFunction("write_file", b_write_file),
        "append_file": BuiltinFunction("append_file", b_append_file),
        "file_exists": BuiltinFunction("file_exists", b_file_exists, 1),
    }
    for name, func in builtins.items():
        env.define(name, func)


BUILTIN_MODULES = {
    "math": make_math_module,
    "random": make_random_module,
    "time": make_time_module,
    "os": make_os_module,
}

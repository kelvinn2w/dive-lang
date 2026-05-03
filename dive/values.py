"""Dive-da iştirak edən dəyər tipləri (funksiya, sinif, instance)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from . import ast_nodes as A
from .environment import Environment
from .errors import NameDiveError, TypeDiveError

if TYPE_CHECKING:  # pragma: no cover
    from .interpreter import Interpreter


class DiveCallable:
    """Çağrıla bilən obyekt protokolu."""

    name: str = "<callable>"

    def call(self, interpreter: "Interpreter", args: list, kwargs: dict) -> object:
        raise NotImplementedError

    def arity(self) -> Optional[int]:
        return None


class BuiltinFunction(DiveCallable):
    def __init__(
        self,
        name: str,
        func: Callable[..., object],
        arity: Optional[int] = None,
    ) -> None:
        self.name = name
        self._func = func
        self._arity = arity

    def call(self, interpreter: "Interpreter", args: list, kwargs: dict) -> object:
        return self._func(*args, **kwargs)

    def arity(self) -> Optional[int]:
        return self._arity

    def __repr__(self) -> str:
        return f"<builtin '{self.name}'>"


class DiveFunction(DiveCallable):
    def __init__(
        self,
        decl: A.FunctionDef,
        closure: Environment,
        is_method: bool = False,
        bound_self: object = None,
    ) -> None:
        self.decl = decl
        self.name = decl.name
        self.closure = closure
        self.is_method = is_method
        self.bound_self = bound_self

    def bind(self, instance: object) -> "DiveFunction":
        return DiveFunction(self.decl, self.closure, is_method=True, bound_self=instance)

    def arity(self) -> Optional[int]:
        return len(self.decl.params)

    def call(self, interpreter: "Interpreter", args: list, kwargs: dict) -> object:
        env = Environment(parent=self.closure)
        params = self.decl.params

        # Method olduqda, ilk parametr (self) avtomatik bağlanır
        positional = list(args)
        if self.is_method and self.bound_self is not None:
            positional = [self.bound_self] + positional

        # Parametrləri bağla
        for i, p in enumerate(params):
            if i < len(positional):
                env.define(p.name, positional[i])
            elif p.name in kwargs:
                env.define(p.name, kwargs.pop(p.name))
            elif p.default is not None:
                env.define(p.name, interpreter.evaluate(p.default))
            else:
                raise TypeDiveError(
                    f"'{self.name}' funksiyası '{p.name}' parametrini gözləyirdi"
                )

        if len(positional) > len(params):
            raise TypeDiveError(
                f"'{self.name}' funksiyası {len(params)} arqument gözləyir, {len(positional)} verildi"
            )
        if kwargs:
            unknown = ", ".join(kwargs.keys())
            raise TypeDiveError(
                f"'{self.name}' funksiyası bu açar arqumentləri tanımır: {unknown}"
            )

        from .errors import ReturnSignal  # lazy

        try:
            interpreter.execute_block(self.decl.body, env)
        except ReturnSignal as r:
            return r.value
        return None

    def __repr__(self) -> str:
        kind = "metod" if self.is_method else "funksiya"
        return f"<{kind} {self.name}>"


class DiveClass(DiveCallable):
    def __init__(
        self,
        name: str,
        methods: Dict[str, DiveFunction],
        bases: List["DiveClass"],
    ) -> None:
        self.name = name
        self.methods = methods
        self.bases = bases

    def find_method(self, name: str) -> Optional[DiveFunction]:
        if name in self.methods:
            return self.methods[name]
        for base in self.bases:
            m = base.find_method(name)
            if m is not None:
                return m
        return None

    def call(self, interpreter: "Interpreter", args: list, kwargs: dict) -> object:
        instance = DiveInstance(self)
        init = self.find_method("init")
        if init is not None:
            init.bind(instance).call(interpreter, args, kwargs)
        else:
            if args or kwargs:
                raise TypeDiveError(
                    f"'{self.name}' sinfinin 'init' metodu yoxdur, lakin arqument verildi"
                )
        return instance

    def arity(self) -> Optional[int]:
        init = self.find_method("init")
        if init is None:
            return 0
        return init.arity()

    def __repr__(self) -> str:
        return f"<class {self.name}>"


class DiveInstance:
    def __init__(self, klass: DiveClass) -> None:
        self.klass = klass
        self.fields: Dict[str, object] = {}

    def get(self, name: str) -> object:
        if name in self.fields:
            return self.fields[name]
        method = self.klass.find_method(name)
        if method is not None:
            return method.bind(self)
        raise NameDiveError(
            f"'{self.klass.name}' obyektində '{name}' atributu yoxdur"
        )

    def set(self, name: str, value: object) -> None:
        self.fields[name] = value

    def __repr__(self) -> str:
        return f"<{self.klass.name} instance>"


class DiveModule:
    """Bir Dive moduluyla onun ad sahəsi."""

    def __init__(self, name: str, env: Environment) -> None:
        self.name = name
        self.env = env

    def get(self, name: str) -> object:
        if name in self.env.values:
            return self.env.values[name]
        raise NameDiveError(f"'{self.name}' modulunda '{name}' yoxdur")

    def __repr__(self) -> str:
        return f"<modul {self.name}>"

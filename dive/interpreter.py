"""Dive dilinin tree-walking interpretatoru."""

from __future__ import annotations

import contextvars
import os
from typing import Dict, List, Optional

from . import ast_nodes as A
from . import builtins as B
from .environment import Environment
from .errors import (
    DiveError,
    BreakSignal,
    ContinueSignal,
    ImportDiveError,
    IndexDiveError,
    NameDiveError,
    ReturnSignal,
    RuntimeDiveError,
    TypeDiveError,
    UserDiveError,
    ValueDiveError,
)
from .lexer import tokenize
from .parser import parse
from .values import DiveCallable, DiveClass, DiveFunction, DiveInstance, DiveModule, BuiltinFunction


# Yardım üçün: built-ins modulları DiveInstance üçün çağırışlar etmək məqsədilə cari interpretora
# çatmaq üçün.
_GLOBAL_INTERPRETER: contextvars.ContextVar[Optional["Interpreter"]] = contextvars.ContextVar(
    "dive_interpreter", default=None
)


def _is_truthy(value: object) -> bool:
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


def _equal(a: object, b: object) -> bool:
    # bool/int qarışıqlığı: true == 1 olur, biz daha sıxıyıq
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    return a == b


class Interpreter:
    def __init__(self, filename: Optional[str] = None) -> None:
        self.globals = Environment()
        self.env = self.globals
        self.filename = filename
        # Modul keş: yol -> DiveModule
        self._module_cache: Dict[str, DiveModule] = {}
        # Hal-hazırda icra olunan faylın yolu (import üçün)
        self._current_file = filename
        B.install_builtins(self.globals)

    # ---------- giriş nöqtələri ----------
    def run(self, source: str, filename: Optional[str] = None) -> object:
        token = _GLOBAL_INTERPRETER.set(self)
        try:
            f = filename or self.filename
            tokens = tokenize(source, filename=f)
            program = parse(tokens, filename=f)
            return self.execute_program(program)
        finally:
            _GLOBAL_INTERPRETER.reset(token)

    def execute_program(self, program: A.Program) -> object:
        result: object = None
        for stmt in program.body:
            result = self.execute(stmt)
        return result

    def execute_block(self, body: List[A.Node], env: Environment) -> None:
        prev = self.env
        self.env = env
        try:
            for stmt in body:
                self.execute(stmt)
        finally:
            self.env = prev

    # ---------- ifadələr (statements) ----------
    def execute(self, node: A.Node) -> object:
        method = getattr(self, f"_exec_{type(node).__name__}", None)
        if method is None:
            raise RuntimeDiveError(
                f"Naməlum ifadə tipi: {type(node).__name__}",
                line=node.line,
                filename=self.filename,
            )
        return method(node)

    def _exec_ExpressionStmt(self, node: A.ExpressionStmt) -> object:
        return self.evaluate(node.expr)

    def _exec_Assign(self, node: A.Assign) -> None:
        value = self.evaluate(node.value)
        for target in node.targets:
            self._assign(target, value)

    def _exec_AugAssign(self, node: A.AugAssign) -> None:
        # Cari dəyəri al
        current = self.evaluate(node.target)
        rhs = self.evaluate(node.value)
        op = node.op[:-1]  # '+=' -> '+'
        new_value = self._binary_op(op, current, rhs, line=node.line)
        self._assign(node.target, new_value)

    def _exec_If(self, node: A.If) -> None:
        if _is_truthy(self.evaluate(node.condition)):
            self.execute_block(node.then_body, Environment(parent=self.env))
            return
        for cond, body in node.elif_clauses:
            if _is_truthy(self.evaluate(cond)):
                self.execute_block(body, Environment(parent=self.env))
                return
        if node.else_body:
            self.execute_block(node.else_body, Environment(parent=self.env))

    def _exec_While(self, node: A.While) -> None:
        while _is_truthy(self.evaluate(node.condition)):
            try:
                self.execute_block(node.body, Environment(parent=self.env))
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def _exec_For(self, node: A.For) -> None:
        iterable = self.evaluate(node.iterable)
        items = self._to_iterable(iterable, line=node.line)
        for item in items:
            inner = Environment(parent=self.env)
            inner.define(node.var, item)
            try:
                self.execute_block(node.body, inner)
            except BreakSignal:
                return
            except ContinueSignal:
                continue

    def _exec_FunctionDef(self, node: A.FunctionDef) -> None:
        func = DiveFunction(node, closure=self.env)
        self.env.define(node.name, func)

    def _exec_ClassDef(self, node: A.ClassDef) -> None:
        bases: List[DiveClass] = []
        for b in node.bases:
            base_val = self.evaluate(b)
            if not isinstance(base_val, DiveClass):
                raise TypeDiveError(
                    f"'{node.name}' sinfi üçün baza sinif olmalıdır",
                    line=node.line,
                )
            bases.append(base_val)
        methods: Dict[str, DiveFunction] = {}
        # Sinif gövdəsini ayrıca env-də icra et: yalnız metodları topla
        body_env = Environment(parent=self.env)
        prev = self.env
        self.env = body_env
        try:
            for stmt in node.body:
                if isinstance(stmt, A.FunctionDef):
                    methods[stmt.name] = DiveFunction(stmt, closure=body_env)
                elif isinstance(stmt, A.Pass):
                    continue
                else:
                    # sinif daxili sahə təyinatları icazəlidir, lakin sadəlik üçün metodlardan
                    # başqa heç nəyə icazə verməsək də, statement-i icra edək (məs. sabitlər)
                    self.execute(stmt)
        finally:
            self.env = prev

        klass = DiveClass(name=node.name, methods=methods, bases=bases)
        self.env.define(node.name, klass)

    def _exec_Return(self, node: A.Return) -> None:
        value = self.evaluate(node.value) if node.value is not None else None
        raise ReturnSignal(value)

    def _exec_Break(self, node: A.Break) -> None:
        raise BreakSignal()

    def _exec_Continue(self, node: A.Continue) -> None:
        raise ContinueSignal()

    def _exec_Pass(self, node: A.Pass) -> None:
        return None

    def _exec_Throw(self, node: A.Throw) -> None:
        value = self.evaluate(node.value)
        if isinstance(value, str):
            raise UserDiveError(value, line=node.line)
        raise UserDiveError(value, line=node.line)

    def _exec_Try(self, node: A.Try) -> None:
        try:
            self.execute_block(node.body, Environment(parent=self.env))
        except (RuntimeDiveError, UserDiveError) as exc:
            if not node.catches:
                if node.finally_body:
                    self.execute_block(node.finally_body, Environment(parent=self.env))
                raise
            # İlk uyğun catch (bizdə tip filtri yoxdur — universal catch)
            clause = node.catches[0]
            inner = Environment(parent=self.env)
            if clause.var:
                err_value: object
                if isinstance(exc, UserDiveError):
                    err_value = exc.value
                else:
                    err_value = exc.message
                inner.define(clause.var, err_value)
            self.execute_block(clause.body, inner)
        finally:
            if node.finally_body:
                self.execute_block(node.finally_body, Environment(parent=self.env))

    def _exec_Import(self, node: A.Import) -> None:
        if node.is_path:
            module = self._import_path(node.target, line=node.line)
            name = node.alias or self._module_name_from_path(node.target)
        else:
            module = self._import_name(node.target, line=node.line)
            name = node.alias or node.target
        self.env.define(name, module)

    # ---------- ifadələr (expressions) ----------
    def evaluate(self, node: A.Node) -> object:
        method = getattr(self, f"_eval_{type(node).__name__}", None)
        if method is None:
            raise RuntimeDiveError(
                f"Naməlum ifadə tipi: {type(node).__name__}",
                line=node.line,
                filename=self.filename,
            )
        return method(node)

    def _eval_NumberLit(self, node: A.NumberLit) -> object:
        return node.value

    def _eval_StringLit(self, node: A.StringLit) -> str:
        return node.value

    def _eval_BoolLit(self, node: A.BoolLit) -> bool:
        return node.value

    def _eval_NoneLit(self, node: A.NoneLit) -> None:
        return None

    def _eval_Identifier(self, node: A.Identifier) -> object:
        try:
            return self.env.get(node.name)
        except NameDiveError as e:
            e.line = node.line
            e.filename = self.filename
            raise

    def _eval_ListLit(self, node: A.ListLit) -> list:
        return [self.evaluate(e) for e in node.elements]

    def _eval_DictLit(self, node: A.DictLit) -> dict:
        out: dict = {}
        for k, v in node.pairs:
            out[self.evaluate(k)] = self.evaluate(v)
        return out

    def _eval_BinaryOp(self, node: A.BinaryOp) -> object:
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        return self._binary_op(node.op, left, right, line=node.line)

    def _eval_UnaryOp(self, node: A.UnaryOp) -> object:
        operand = self.evaluate(node.operand)
        if node.op == "-":
            if isinstance(operand, (int, float)) and not isinstance(operand, bool):
                return -operand
            raise TypeDiveError("'-' yalnız ədədlərə tətbiq olunur", line=node.line)
        if node.op == "+":
            if isinstance(operand, (int, float)) and not isinstance(operand, bool):
                return +operand
            raise TypeDiveError("'+' yalnız ədədlərə tətbiq olunur", line=node.line)
        if node.op == "not":
            return not _is_truthy(operand)
        raise RuntimeDiveError(f"Naməlum unar operator: {node.op}", line=node.line)

    def _eval_LogicalOp(self, node: A.LogicalOp) -> object:
        left = self.evaluate(node.left)
        if node.op == "and":
            if not _is_truthy(left):
                return left
            return self.evaluate(node.right)
        if node.op == "or":
            if _is_truthy(left):
                return left
            return self.evaluate(node.right)
        raise RuntimeDiveError(f"Naməlum məntiqi operator: {node.op}", line=node.line)

    def _eval_Compare(self, node: A.Compare) -> bool:
        left = self.evaluate(node.left)
        for op, right_node in zip(node.ops, node.comparators):
            right = self.evaluate(right_node)
            if not self._compare(op, left, right, line=node.line):
                return False
            left = right
        return True

    def _eval_Call(self, node: A.Call) -> object:
        func = self.evaluate(node.func)
        args = [self.evaluate(a) for a in node.args]
        kwargs = {name: self.evaluate(v) for name, v in node.kwargs}
        return self._call(func, args, kwargs, line=node.line)

    def _eval_Attribute(self, node: A.Attribute) -> object:
        obj = self.evaluate(node.obj)
        return self._get_attribute(obj, node.name, line=node.line)

    def _eval_Subscript(self, node: A.Subscript) -> object:
        obj = self.evaluate(node.obj)
        index = self.evaluate(node.index) if not isinstance(node.index, A.Slice) else self._eval_slice_value(node.index)
        return self._get_subscript(obj, index, line=node.line)

    def _eval_Slice(self, node: A.Slice) -> slice:
        start = self.evaluate(node.start) if node.start is not None else None
        stop = self.evaluate(node.stop) if node.stop is not None else None
        step = self.evaluate(node.step) if node.step is not None else None
        return slice(start, stop, step)

    def _eval_slice_value(self, node: A.Slice) -> slice:
        return self._eval_Slice(node)

    def _eval_Lambda(self, node: A.Lambda) -> DiveFunction:
        # Lambda-nı normal funksiya kimi qur
        body_stmt = A.Return(line=node.line, value=node.body)
        params = [A.Param(line=node.line, name=p) for p in node.params]
        decl = A.FunctionDef(
            line=node.line, name="<lambda>", params=params, body=[body_stmt]
        )
        return DiveFunction(decl, closure=self.env)

    # ---------- yardımçı ----------
    def _binary_op(self, op: str, left: object, right: object, line: int) -> object:
        try:
            if op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    return _ensure_string(left, right)
                if isinstance(left, list) and isinstance(right, list):
                    return left + right
                if isinstance(left, bool) or isinstance(right, bool):
                    raise TypeDiveError("'+' bool-larla istifadə oluna bilməz")
                return left + right
            if op == "-":
                _check_num(left, right, "-")
                return left - right
            if op == "*":
                if isinstance(left, str) and isinstance(right, int):
                    return left * right
                if isinstance(left, int) and isinstance(right, str):
                    return right * left
                if isinstance(left, list) and isinstance(right, int):
                    return left * right
                if isinstance(left, int) and isinstance(right, list):
                    return right * left
                _check_num(left, right, "*")
                return left * right
            if op == "/":
                _check_num(left, right, "/")
                if right == 0:
                    raise ValueDiveError("Sıfıra bölmə")
                return left / right
            if op == "//":
                _check_num(left, right, "//")
                if right == 0:
                    raise ValueDiveError("Sıfıra bölmə")
                return left // right
            if op == "%":
                _check_num(left, right, "%")
                if right == 0:
                    raise ValueDiveError("Sıfıra bölmə (mod)")
                return left % right
            if op == "**":
                _check_num(left, right, "**")
                return left ** right
        except TypeDiveError as e:
            e.line = line
            e.filename = self.filename
            raise
        except ValueDiveError as e:
            e.line = line
            e.filename = self.filename
            raise
        raise RuntimeDiveError(f"Naməlum operator: {op}", line=line)

    def _compare(self, op: str, left: object, right: object, line: int) -> bool:
        try:
            if op == "==":
                return _equal(left, right)
            if op == "!=":
                return not _equal(left, right)
            if op == "in":
                if isinstance(right, (list, str)):
                    return left in right
                if isinstance(right, dict):
                    return left in right
                raise TypeDiveError(f"'in' bu tipə tətbiq olunmur: {type(right).__name__}")
            if op == "not in":
                if isinstance(right, (list, str)):
                    return left not in right
                if isinstance(right, dict):
                    return left not in right
                raise TypeDiveError(f"'not in' bu tipə tətbiq olunmur: {type(right).__name__}")
            if op in ("<", ">", "<=", ">="):
                if isinstance(left, str) and isinstance(right, str):
                    pass
                elif (isinstance(left, (int, float)) and not isinstance(left, bool)
                      and isinstance(right, (int, float)) and not isinstance(right, bool)):
                    pass
                else:
                    raise TypeDiveError(
                        f"'{op}' uyğun olmayan tiplərə tətbiq olunur: "
                        f"{type(left).__name__} və {type(right).__name__}"
                    )
                if op == "<":
                    return left < right
                if op == ">":
                    return left > right
                if op == "<=":
                    return left <= right
                if op == ">=":
                    return left >= right
        except TypeDiveError as e:
            e.line = line
            e.filename = self.filename
            raise
        raise RuntimeDiveError(f"Naməlum müqayisə operatoru: {op}", line=line)

    def _to_iterable(self, value: object, line: int) -> list:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return list(value)
        if isinstance(value, dict):
            return list(value.keys())
        raise TypeDiveError(
            f"İterasiya olunan tip gözlənilirdi (list/string/dict), {type(value).__name__} tapıldı",
            line=line,
            filename=self.filename,
        )

    def _call(self, func: object, args: list, kwargs: dict, line: int) -> object:
        if isinstance(func, DiveCallable):
            try:
                return func.call(self, args, kwargs)
            except DiveError as e:
                if e.line is None:
                    e.line = line
                if e.filename is None:
                    e.filename = self.filename
                raise
        raise TypeDiveError(
            f"Çağrıla bilməyən obyekt: {type(func).__name__}",
            line=line,
            filename=self.filename,
        )

    def _get_attribute(self, obj: object, name: str, line: int) -> object:
        if isinstance(obj, DiveInstance):
            try:
                return obj.get(name)
            except NameDiveError as e:
                e.line = line
                e.filename = self.filename
                raise
        if isinstance(obj, DiveClass):
            method = obj.find_method(name)
            if method is not None:
                return method
            raise NameDiveError(
                f"'{obj.name}' sinfində '{name}' metodu yoxdur",
                line=line,
                filename=self.filename,
            )
        if isinstance(obj, DiveModule):
            try:
                return obj.get(name)
            except NameDiveError as e:
                e.line = line
                e.filename = self.filename
                raise
        if isinstance(obj, str):
            m = B.string_method(name, obj)
            if m is not None:
                return m
        if isinstance(obj, list):
            m = B.list_method(name, obj)
            if m is not None:
                return m
        if isinstance(obj, dict):
            m = B.dict_method(name, obj)
            if m is not None:
                return m
        if isinstance(obj, B.DiveFile):
            m = B.file_method(name, obj)
            if m is not None:
                return m
        raise NameDiveError(
            f"'{type(obj).__name__}' tipində '{name}' atributu yoxdur",
            line=line,
            filename=self.filename,
        )

    def _get_subscript(self, obj: object, index: object, line: int) -> object:
        try:
            if isinstance(obj, list):
                if isinstance(index, slice):
                    return obj[index]
                if not isinstance(index, int):
                    raise TypeDiveError("Siyahı indeksi tam ədəd olmalıdır")
                return obj[index]
            if isinstance(obj, str):
                if isinstance(index, slice):
                    return obj[index]
                if not isinstance(index, int):
                    raise TypeDiveError("String indeksi tam ədəd olmalıdır")
                return obj[index]
            if isinstance(obj, dict):
                if index not in obj:
                    raise IndexDiveError(f"Açar tapılmadı: {index!r}")
                return obj[index]
        except IndexError:
            raise IndexDiveError(
                f"İndeks həddən kənardır: {index}",
                line=line,
                filename=self.filename,
            )
        except (TypeDiveError, IndexDiveError) as e:
            e.line = line
            e.filename = self.filename
            raise
        raise TypeDiveError(
            f"İndeksləmə bu tipə tətbiq olunmur: {type(obj).__name__}",
            line=line,
            filename=self.filename,
        )

    def _assign(self, target: A.Node, value: object) -> None:
        if isinstance(target, A.Identifier):
            if self.env.has(target.name):
                self.env.set(target.name, value)
            else:
                self.env.define(target.name, value)
            return
        if isinstance(target, A.Attribute):
            obj = self.evaluate(target.obj)
            if isinstance(obj, DiveInstance):
                obj.set(target.name, value)
                return
            raise TypeDiveError(
                f"Atribut təyini bu tipə tətbiq olunmur: {type(obj).__name__}",
                line=target.line,
                filename=self.filename,
            )
        if isinstance(target, A.Subscript):
            obj = self.evaluate(target.obj)
            index = self.evaluate(target.index) if not isinstance(target.index, A.Slice) else self._eval_slice_value(target.index)
            if isinstance(obj, list):
                if not isinstance(index, int):
                    raise TypeDiveError("Siyahı indeksi tam ədəd olmalıdır", line=target.line)
                try:
                    obj[index] = value
                except IndexError:
                    raise IndexDiveError(f"İndeks həddən kənardır: {index}", line=target.line)
                return
            if isinstance(obj, dict):
                obj[index] = value
                return
            raise TypeDiveError(
                f"İndekslə təyin bu tipə tətbiq olunmur: {type(obj).__name__}",
                line=target.line,
                filename=self.filename,
            )
        raise TypeDiveError(
            f"Bu ifadəyə təyin edilə bilməz: {type(target).__name__}",
            line=target.line,
            filename=self.filename,
        )

    # ---------- import ----------
    def _module_name_from_path(self, path: str) -> str:
        base = os.path.basename(path)
        if base.endswith(".dive"):
            base = base[: -len(".dive")]
        return base

    def _import_name(self, name: str, line: int) -> DiveModule:
        # Önce builtin modullar
        factory = B.BUILTIN_MODULES.get(name)
        if factory is not None:
            if name not in self._module_cache:
                self._module_cache[name] = factory()
            return self._module_cache[name]
        # Sonra cari qovluqda <name>.dive axtarmaq
        candidate = name + ".dive"
        return self._import_path(candidate, line=line)

    def _import_path(self, target: str, line: int) -> DiveModule:
        # Yolu həll et: cari fayla nisbətdə
        base_dir = "."
        if self._current_file:
            base_dir = os.path.dirname(os.path.abspath(self._current_file)) or "."
        full_path = target
        if not os.path.isabs(target):
            full_path = os.path.normpath(os.path.join(base_dir, target))
        if full_path in self._module_cache:
            return self._module_cache[full_path]
        if not os.path.exists(full_path):
            # Cari iş qovluğunda da axtaraq
            alt = os.path.normpath(os.path.join(os.getcwd(), target))
            if os.path.exists(alt):
                full_path = alt
            else:
                raise ImportDiveError(
                    f"Modul tapılmadı: {target}",
                    line=line,
                    filename=self.filename,
                )
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                source = f.read()
        except OSError as e:
            raise ImportDiveError(f"Modulu oxumaq mümkün olmadı: {e}", line=line)
        # Modulu öz environment-ində icra et
        module_env = Environment(parent=self.globals)
        # Built-in-lər zaten globals-da var
        prev_file = self._current_file
        prev_env = self.env
        self._current_file = full_path
        self.env = module_env
        try:
            tokens = tokenize(source, filename=full_path)
            program = parse(tokens, filename=full_path)
            self.execute_program(program)
        finally:
            self.env = prev_env
            self._current_file = prev_file
        module = DiveModule(self._module_name_from_path(full_path), module_env)
        self._module_cache[full_path] = module
        return module


# ---------- köməkçi tip yoxlamaları ----------


def _check_num(a: object, b: object, op: str) -> None:
    if isinstance(a, bool) or isinstance(b, bool):
        raise TypeDiveError(f"'{op}' bool-larla istifadə oluna bilməz")
    if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        raise TypeDiveError(
            f"'{op}' yalnız ədədlərə tətbiq olunur, '{type(a).__name__}' və '{type(b).__name__}' verildi"
        )


def _ensure_string(a: object, b: object) -> str:
    if isinstance(a, str) and isinstance(b, str):
        return a + b
    raise TypeDiveError(
        f"'+' string ilə uyğun olmayan tip arasında: {type(a).__name__} və {type(b).__name__}"
    )

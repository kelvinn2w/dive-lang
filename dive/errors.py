"""Dive dilində xətalar (errors)."""

from __future__ import annotations

from typing import Optional


class DiveError(Exception):
    """Dive-da bütün xətaların əsas sinfi."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        filename: Optional[str] = None,
    ) -> None:
        self.message = message
        self.line = line
        self.column = column
        self.filename = filename
        super().__init__(self._format())

    def _format(self) -> str:
        loc_parts = []
        if self.filename:
            loc_parts.append(self.filename)
        if self.line is not None:
            loc_parts.append(f"sətir {self.line}")
        if self.column is not None:
            loc_parts.append(f"sütun {self.column}")
        loc = ", ".join(loc_parts)
        prefix = f"[{loc}] " if loc else ""
        return f"{prefix}{self.kind}: {self.message}"

    @property
    def kind(self) -> str:
        return "Xəta"


class LexerError(DiveError):
    @property
    def kind(self) -> str:
        return "LeksikXətası"


class ParseError(DiveError):
    @property
    def kind(self) -> str:
        return "SintaksisXətası"


class RuntimeDiveError(DiveError):
    @property
    def kind(self) -> str:
        return "İcraXətası"


class NameDiveError(RuntimeDiveError):
    @property
    def kind(self) -> str:
        return "AdXətası"


class TypeDiveError(RuntimeDiveError):
    @property
    def kind(self) -> str:
        return "TipXətası"


class ValueDiveError(RuntimeDiveError):
    @property
    def kind(self) -> str:
        return "DəyərXətası"


class IndexDiveError(RuntimeDiveError):
    @property
    def kind(self) -> str:
        return "IndeksXətası"


class ImportDiveError(RuntimeDiveError):
    @property
    def kind(self) -> str:
        return "İmportXətası"


class UserDiveError(RuntimeDiveError):
    """`throw` ilə istifadəçi tərəfindən atılan xəta."""

    def __init__(self, value: object, line: Optional[int] = None) -> None:
        self.value = value
        super().__init__(str(value), line=line)

    @property
    def kind(self) -> str:
        return "İstifadəçiXətası"


class BreakSignal(Exception):
    """Daxili siqnal: `break`."""


class ContinueSignal(Exception):
    """Daxili siqnal: `continue`."""


class ReturnSignal(Exception):
    """Daxili siqnal: `return value`."""

    def __init__(self, value: object) -> None:
        self.value = value

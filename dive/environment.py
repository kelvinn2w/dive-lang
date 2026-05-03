"""Dive üçün dəyişən scope-ları (environment)."""

from __future__ import annotations

from typing import Dict, Optional

from .errors import NameDiveError


class Environment:
    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self.values: Dict[str, object] = {}
        self.parent = parent

    def define(self, name: str, value: object) -> None:
        self.values[name] = value

    def get(self, name: str) -> object:
        env: Optional[Environment] = self
        while env is not None:
            if name in env.values:
                return env.values[name]
            env = env.parent
        raise NameDiveError(f"'{name}' təyin edilməyib")

    def set(self, name: str, value: object) -> None:
        """Mövcud bir adı yenilə (əgər varsa); yoxdursa cari scope-da təyin et."""
        env: Optional[Environment] = self
        while env is not None:
            if name in env.values:
                env.values[name] = value
                return
            env = env.parent
        self.values[name] = value

    def has(self, name: str) -> bool:
        env: Optional[Environment] = self
        while env is not None:
            if name in env.values:
                return True
            env = env.parent
        return False

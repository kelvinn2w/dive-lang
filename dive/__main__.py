"""Dive CLI: `python -m dive program.dive` və ya `dive program.dive`."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from . import __version__
from .errors import DiveError
from .interpreter import Interpreter


def run_file(path: str) -> int:
    if not os.path.exists(path):
        print(f"Xəta: fayl tapılmadı: {path}", file=sys.stderr)
        return 2
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    interp = Interpreter(filename=path)
    try:
        interp.run(source, filename=path)
    except DiveError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


def run_repl() -> int:
    print(f"Dive {__version__} REPL — çıxmaq üçün Ctrl-D və ya 'exit'")
    interp = Interpreter(filename="<repl>")
    buffer: List[str] = []
    prompt = ">>> "
    while True:
        try:
            line = input(prompt)
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print("\n(KeyboardInterrupt)")
            buffer = []
            prompt = ">>> "
            continue
        if not buffer and line.strip() in ("exit", "quit"):
            return 0
        buffer.append(line)
        # Çoxsətirli blok: sətrin sonu ':' ilə bitirsə, daha çox sətir oxu
        joined = "\n".join(buffer)
        if line.endswith(":") or (buffer and line.startswith((" ", "\t"))):
            prompt = "... "
            if line.strip() == "":
                # Boş sətir: blokun sonunu göstərir
                pass
            else:
                continue
        if line.strip() == "" and buffer[-1].strip() == "":
            # Boş sətir blokun sonunu göstərir
            pass
        elif line.endswith(":"):
            continue
        try:
            interp.run(joined + "\n", filename="<repl>")
        except DiveError as e:
            print(str(e), file=sys.stderr)
        buffer = []
        prompt = ">>> "


def run_string(source: str) -> int:
    interp = Interpreter(filename="<string>")
    try:
        interp.run(source, filename="<string>")
    except DiveError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="dive", description="Dive proqramlaşdırma dili")
    parser.add_argument("file", nargs="?", help="İcra ediləcək .dive faylı")
    parser.add_argument("-c", "--code", help="Komandadan birbaşa kod icra et")
    parser.add_argument("-v", "--version", action="version", version=f"Dive {__version__}")
    args = parser.parse_args(argv)

    if args.code:
        return run_string(args.code)
    if args.file:
        return run_file(args.file)
    return run_repl()


if __name__ == "__main__":
    sys.exit(main())

"""Dive dili üçün leksik analizator (tokenizer)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

from .errors import LexerError


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENT = auto()

    # Keywords
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    FUNCTION = auto()
    RETURN = auto()
    CLASS = auto()
    IMPORT = auto()
    AS = auto()
    FROM = auto()
    TRUE = auto()
    FALSE = auto()
    NONE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    TRY = auto()
    CATCH = auto()
    FINALLY = auto()
    THROW = auto()
    BREAK = auto()
    CONTINUE = auto()
    PASS = auto()
    LAMBDA = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    DSLASH = auto()  # //
    PERCENT = auto()
    DSTAR = auto()  # **
    ASSIGN = auto()  # =
    EQ = auto()  # ==
    NEQ = auto()  # !=
    LT = auto()
    GT = auto()
    LEQ = auto()
    GEQ = auto()
    PLUS_EQ = auto()
    MINUS_EQ = auto()
    STAR_EQ = auto()
    SLASH_EQ = auto()
    PERCENT_EQ = auto()

    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACK = auto()
    RBRACK = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    COLON = auto()
    DOT = auto()
    ARROW = auto()  # ->

    # Indentation / structure
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()


KEYWORDS = {
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "function": TokenType.FUNCTION,
    "return": TokenType.RETURN,
    "class": TokenType.CLASS,
    "import": TokenType.IMPORT,
    "as": TokenType.AS,
    "from": TokenType.FROM,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "none": TokenType.NONE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "try": TokenType.TRY,
    "catch": TokenType.CATCH,
    "finally": TokenType.FINALLY,
    "throw": TokenType.THROW,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "pass": TokenType.PASS,
    "lambda": TokenType.LAMBDA,
}


@dataclass
class Token:
    type: TokenType
    value: object
    line: int
    column: int

    def __repr__(self) -> str:  # pragma: no cover - sadə debug
        return f"Token({self.type.name}, {self.value!r}, sətir={self.line})"


class Lexer:
    def __init__(self, source: str, filename: Optional[str] = None) -> None:
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
        self.indent_stack: List[int] = [0]
        self.paren_depth = 0  # () [] {} içində NEWLINE/INDENT vermirik
        self.at_line_start = True

    # ---------- köməkçi metodlar ----------
    def _peek(self, offset: int = 0) -> str:
        i = self.pos + offset
        if i >= len(self.source):
            return ""
        return self.source[i]

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def _err(self, msg: str) -> LexerError:
        return LexerError(msg, line=self.line, column=self.col, filename=self.filename)

    def _add(self, type_: TokenType, value: object = None, line: Optional[int] = None,
             column: Optional[int] = None) -> None:
        self.tokens.append(
            Token(
                type=type_,
                value=value,
                line=line if line is not None else self.line,
                column=column if column is not None else self.col,
            )
        )

    # ---------- əsas tokenize loop ----------
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            if self.at_line_start and self.paren_depth == 0:
                self._handle_indentation()
                self.at_line_start = False
                if self.pos >= len(self.source):
                    break
                # Boş sətir / yalnız şərh idi və indent_stack dəyişdi
                # Davam edirik

            ch = self._peek()
            if ch == "":
                break

            if ch == "\n":
                if self.paren_depth == 0:
                    self._add(TokenType.NEWLINE, "\\n")
                    self._advance()
                    self.at_line_start = True
                else:
                    self._advance()
                continue

            if ch in " \t":
                self._advance()
                continue

            if ch == "#":
                while self._peek() and self._peek() != "\n":
                    self._advance()
                continue

            if ch == "\\" and self._peek(1) == "\n":
                # Sətir davamı
                self._advance()
                self._advance()
                continue

            if ch.isdigit() or (ch == "." and self._peek(1).isdigit()):
                self._number()
                continue

            if ch.isalpha() or ch == "_":
                self._identifier()
                continue

            if ch == '"' or ch == "'":
                self._string(ch)
                continue

            self._operator_or_punct()

        # Faylın sonunda NEWLINE əlavə et (əgər yoxdursa)
        if self.tokens and self.tokens[-1].type != TokenType.NEWLINE:
            self._add(TokenType.NEWLINE, "\\n")

        # Qalan indent-ləri DEDENT et
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self._add(TokenType.DEDENT)

        self._add(TokenType.EOF)
        return self.tokens

    # ---------- indent ----------
    def _handle_indentation(self) -> None:
        # Boş sətirləri və şərhləri keç
        while True:
            line_start = self.pos
            indent = 0
            while self._peek() == " " or self._peek() == "\t":
                if self._peek() == "\t":
                    indent += 8 - (indent % 8)
                else:
                    indent += 1
                self._advance()
            ch = self._peek()
            if ch == "\n":
                self._advance()
                continue
            if ch == "#":
                while self._peek() and self._peek() != "\n":
                    self._advance()
                continue
            if ch == "":
                return
            # gerçək məzmunlu sətirdir
            break

        current = self.indent_stack[-1]
        if indent > current:
            self.indent_stack.append(indent)
            self._add(TokenType.INDENT)
        else:
            while indent < self.indent_stack[-1]:
                self.indent_stack.pop()
                self._add(TokenType.DEDENT)
            if indent != self.indent_stack[-1]:
                raise self._err(
                    f"Girinti uyğunsuzluğu: {indent} boşluq, gözlənilirdi {self.indent_stack[-1]}"
                )

    # ---------- ədədlər ----------
    def _number(self) -> None:
        start_line, start_col = self.line, self.col
        start = self.pos
        is_float = False
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek(1).isdigit():
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()
        if self._peek() in ("e", "E"):
            is_float = True
            self._advance()
            if self._peek() in ("+", "-"):
                self._advance()
            if not self._peek().isdigit():
                raise self._err("Ədədin eksponent hissəsi düzgün deyil")
            while self._peek().isdigit():
                self._advance()
        text = self.source[start : self.pos]
        value: object = float(text) if is_float else int(text)
        self.tokens.append(
            Token(TokenType.NUMBER, value, start_line, start_col)
        )

    # ---------- identifikator / açar söz ----------
    def _identifier(self) -> None:
        start_line, start_col = self.line, self.col
        start = self.pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.source[start : self.pos]
        kw = KEYWORDS.get(text)
        if kw is not None:
            value: object
            if kw == TokenType.TRUE:
                value = True
            elif kw == TokenType.FALSE:
                value = False
            elif kw == TokenType.NONE:
                value = None
            else:
                value = text
            self.tokens.append(Token(kw, value, start_line, start_col))
        else:
            self.tokens.append(Token(TokenType.IDENT, text, start_line, start_col))

    # ---------- string ----------
    def _string(self, quote: str) -> None:
        start_line, start_col = self.line, self.col
        self._advance()  # quote
        # Triple-quoted string?
        triple = False
        if self._peek() == quote and self._peek(1) == quote:
            self._advance()
            self._advance()
            triple = True

        out = []
        while True:
            ch = self._peek()
            if ch == "":
                raise self._err("Bağlanmamış string literali")
            if not triple and ch == "\n":
                raise self._err("Bağlanmamış string literali (sətir bitdi)")
            if ch == "\\":
                self._advance()
                esc = self._advance()
                mapping = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    "0": "\0",
                    "\\": "\\",
                    '"': '"',
                    "'": "'",
                    "a": "\a",
                    "b": "\b",
                    "f": "\f",
                    "v": "\v",
                }
                if esc in mapping:
                    out.append(mapping[esc])
                elif esc == "\n":
                    pass  # qaçırılan sətir kəsmi
                else:
                    out.append("\\" + esc)
                continue
            if triple:
                if ch == quote and self._peek(1) == quote and self._peek(2) == quote:
                    self._advance(); self._advance(); self._advance()
                    break
                out.append(self._advance())
            else:
                if ch == quote:
                    self._advance()
                    break
                out.append(self._advance())

        self.tokens.append(
            Token(TokenType.STRING, "".join(out), start_line, start_col)
        )

    # ---------- operator / punctuation ----------
    def _operator_or_punct(self) -> None:
        line, col = self.line, self.col
        ch = self._advance()

        def emit(type_: TokenType, value: object = None) -> None:
            self.tokens.append(Token(type_, value if value is not None else ch, line, col))

        if ch == "+":
            if self._match("="):
                emit(TokenType.PLUS_EQ, "+=")
            else:
                emit(TokenType.PLUS, "+")
        elif ch == "-":
            if self._match("="):
                emit(TokenType.MINUS_EQ, "-=")
            elif self._match(">"):
                emit(TokenType.ARROW, "->")
            else:
                emit(TokenType.MINUS, "-")
        elif ch == "*":
            if self._match("*"):
                emit(TokenType.DSTAR, "**")
            elif self._match("="):
                emit(TokenType.STAR_EQ, "*=")
            else:
                emit(TokenType.STAR, "*")
        elif ch == "/":
            if self._match("/"):
                emit(TokenType.DSLASH, "//")
            elif self._match("="):
                emit(TokenType.SLASH_EQ, "/=")
            else:
                emit(TokenType.SLASH, "/")
        elif ch == "%":
            if self._match("="):
                emit(TokenType.PERCENT_EQ, "%=")
            else:
                emit(TokenType.PERCENT, "%")
        elif ch == "=":
            if self._match("="):
                emit(TokenType.EQ, "==")
            else:
                emit(TokenType.ASSIGN, "=")
        elif ch == "!":
            if self._match("="):
                emit(TokenType.NEQ, "!=")
            else:
                raise self._err("Gözlənilməz simvol '!'")
        elif ch == "<":
            if self._match("="):
                emit(TokenType.LEQ, "<=")
            else:
                emit(TokenType.LT, "<")
        elif ch == ">":
            if self._match("="):
                emit(TokenType.GEQ, ">=")
            else:
                emit(TokenType.GT, ">")
        elif ch == "(":
            self.paren_depth += 1
            emit(TokenType.LPAREN, "(")
        elif ch == ")":
            self.paren_depth = max(0, self.paren_depth - 1)
            emit(TokenType.RPAREN, ")")
        elif ch == "[":
            self.paren_depth += 1
            emit(TokenType.LBRACK, "[")
        elif ch == "]":
            self.paren_depth = max(0, self.paren_depth - 1)
            emit(TokenType.RBRACK, "]")
        elif ch == "{":
            self.paren_depth += 1
            emit(TokenType.LBRACE, "{")
        elif ch == "}":
            self.paren_depth = max(0, self.paren_depth - 1)
            emit(TokenType.RBRACE, "}")
        elif ch == ",":
            emit(TokenType.COMMA, ",")
        elif ch == ":":
            emit(TokenType.COLON, ":")
        elif ch == ".":
            emit(TokenType.DOT, ".")
        else:
            raise LexerError(
                f"Tanınmayan simvol {ch!r}",
                line=line,
                column=col,
                filename=self.filename,
            )


def tokenize(source: str, filename: Optional[str] = None) -> List[Token]:
    return Lexer(source, filename=filename).tokenize()

"""Lexer testləri."""

from dive.lexer import tokenize, TokenType


def types(source: str) -> list:
    return [t.type for t in tokenize(source)]


def test_simple_tokens():
    ts = tokenize("x = 1 + 2")
    assert ts[0].type == TokenType.IDENT and ts[0].value == "x"
    assert ts[1].type == TokenType.ASSIGN
    assert ts[2].type == TokenType.NUMBER and ts[2].value == 1
    assert ts[3].type == TokenType.PLUS
    assert ts[4].type == TokenType.NUMBER and ts[4].value == 2


def test_string_literal():
    ts = tokenize('s = "salam\\n"')
    assert ts[2].type == TokenType.STRING
    assert ts[2].value == "salam\n"


def test_keywords():
    src = "if x: return true"
    ts = tokenize(src)
    kinds = [t.type for t in ts]
    assert TokenType.IF in kinds
    assert TokenType.RETURN in kinds
    assert TokenType.TRUE in kinds


def test_indentation():
    src = "if x:\n    y = 1\n    z = 2\nw = 3\n"
    ts = tokenize(src)
    kinds = [t.type for t in ts]
    assert TokenType.INDENT in kinds
    assert TokenType.DEDENT in kinds


def test_float_and_exponent():
    ts = tokenize("a = 1.5\nb = 2e3\nc = 3.14e-2\n")
    nums = [t.value for t in ts if t.type == TokenType.NUMBER]
    assert nums == [1.5, 2000.0, 3.14e-2]


def test_comments_skipped():
    src = "# bu şərhdir\nx = 1\n"
    ts = tokenize(src)
    # ilk token ya NEWLINE ya da IDENT olmalıdır
    # Şərhdən sonrakı boş sətir keçilir
    nonws = [t for t in ts if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
    assert nonws[0].type == TokenType.IDENT

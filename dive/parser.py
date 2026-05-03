"""Dive dili üçün rekursiv eniş parseri (recursive descent)."""

from __future__ import annotations

from typing import List, Optional, Tuple

from . import ast_nodes as A
from .errors import ParseError
from .lexer import Token, TokenType as T


class Parser:
    def __init__(self, tokens: List[Token], filename: Optional[str] = None) -> None:
        self.tokens = tokens
        self.pos = 0
        self.filename = filename

    # ---------- köməkçi ----------
    def _peek(self, offset: int = 0) -> Token:
        i = self.pos + offset
        if i >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[i]

    def _check(self, *types: T) -> bool:
        return self._peek().type in types

    def _match(self, *types: T) -> Optional[Token]:
        if self._check(*types):
            tok = self.tokens[self.pos]
            self.pos += 1
            return tok
        return None

    def _expect(self, type_: T, message: Optional[str] = None) -> Token:
        tok = self._peek()
        if tok.type != type_:
            msg = message or f"Gözlənilirdi {type_.name}, tapıldı {tok.type.name} ({tok.value!r})"
            raise ParseError(msg, line=tok.line, column=tok.column, filename=self.filename)
        self.pos += 1
        return tok

    def _err(self, msg: str, tok: Optional[Token] = None) -> ParseError:
        t = tok or self._peek()
        return ParseError(msg, line=t.line, column=t.column, filename=self.filename)

    def _skip_newlines(self) -> None:
        while self._match(T.NEWLINE):
            pass

    # ---------- giriş nöqtəsi ----------
    def parse(self) -> A.Program:
        body: List[A.Node] = []
        self._skip_newlines()
        while not self._check(T.EOF):
            stmt = self._parse_statement()
            if stmt is not None:
                if isinstance(stmt, list):
                    body.extend(stmt)
                else:
                    body.append(stmt)
            self._skip_newlines()
        return A.Program(line=1, body=body)

    # ---------- ifadələr (statements) ----------
    def _parse_statement(self) -> Optional[A.Node]:
        tok = self._peek()
        t = tok.type
        if t == T.IF:
            return self._parse_if()
        if t == T.WHILE:
            return self._parse_while()
        if t == T.FOR:
            return self._parse_for()
        if t == T.FUNCTION:
            return self._parse_function_def()
        if t == T.CLASS:
            return self._parse_class_def()
        if t == T.TRY:
            return self._parse_try()
        if t == T.IMPORT:
            stmt = self._parse_import()
            self._consume_end_of_stmt()
            return stmt
        if t == T.RETURN:
            return self._parse_return()
        if t == T.THROW:
            return self._parse_throw()
        if t == T.BREAK:
            self.pos += 1
            self._consume_end_of_stmt()
            return A.Break(line=tok.line)
        if t == T.CONTINUE:
            self.pos += 1
            self._consume_end_of_stmt()
            return A.Continue(line=tok.line)
        if t == T.PASS:
            self.pos += 1
            self._consume_end_of_stmt()
            return A.Pass(line=tok.line)
        return self._parse_expr_or_assign()

    def _consume_end_of_stmt(self) -> None:
        if self._check(T.NEWLINE) or self._check(T.EOF) or self._check(T.DEDENT):
            self._match(T.NEWLINE)
            return
        tok = self._peek()
        raise self._err(
            f"Sətrin sonu gözlənilirdi, tapıldı {tok.type.name} ({tok.value!r})",
            tok,
        )

    def _parse_block(self) -> List[A.Node]:
        # block ::= ":" NEWLINE INDENT statement+ DEDENT
        self._expect(T.COLON, "':' gözlənilirdi")
        # Tek sətirli blok? `if x: do_thing()`  -> destək vermirik, sadəlik üçün
        if not self._check(T.NEWLINE):
            # tek sətirli
            stmts: List[A.Node] = []
            stmt = self._parse_statement()
            if stmt is not None:
                if isinstance(stmt, list):
                    stmts.extend(stmt)
                else:
                    stmts.append(stmt)
            return stmts
        self._expect(T.NEWLINE)
        self._skip_newlines()
        self._expect(T.INDENT, "Bloka girinti (indent) gözlənilirdi")
        body: List[A.Node] = []
        self._skip_newlines()
        while not self._check(T.DEDENT) and not self._check(T.EOF):
            stmt = self._parse_statement()
            if stmt is not None:
                if isinstance(stmt, list):
                    body.extend(stmt)
                else:
                    body.append(stmt)
            self._skip_newlines()
        self._match(T.DEDENT)
        if not body:
            tok = self._peek()
            raise self._err("Boş blok (heç olmasa bir ifadə tələb olunur)", tok)
        return body

    def _parse_if(self) -> A.If:
        tok = self._expect(T.IF)
        cond = self._parse_expr()
        then_body = self._parse_block()
        elif_clauses: List[Tuple[A.Node, List[A.Node]]] = []
        else_body: List[A.Node] = []
        # Bloklardan sonra newlines/dedents skip oluna bilər
        # Davam edən elif/else aşkarlamaq üçün
        while True:
            # Möhkəm: növbəti significant token-ə baxaq
            saved = self.pos
            self._skip_newlines()
            if self._check(T.ELIF):
                self._match(T.ELIF)
                ec = self._parse_expr()
                eb = self._parse_block()
                elif_clauses.append((ec, eb))
                continue
            if self._check(T.ELSE):
                self._match(T.ELSE)
                else_body = self._parse_block()
                break
            self.pos = saved
            break
        return A.If(
            line=tok.line,
            condition=cond,
            then_body=then_body,
            elif_clauses=elif_clauses,
            else_body=else_body,
        )

    def _parse_while(self) -> A.While:
        tok = self._expect(T.WHILE)
        cond = self._parse_expr()
        body = self._parse_block()
        return A.While(line=tok.line, condition=cond, body=body)

    def _parse_for(self) -> A.For:
        tok = self._expect(T.FOR)
        ident = self._expect(T.IDENT, "for döngüsündə dəyişən adı gözlənilirdi")
        self._expect(T.IN, "'in' gözlənilirdi")
        iterable = self._parse_expr()
        body = self._parse_block()
        return A.For(line=tok.line, var=str(ident.value), iterable=iterable, body=body)

    def _parse_function_def(self) -> A.FunctionDef:
        tok = self._expect(T.FUNCTION)
        name_tok = self._expect(T.IDENT, "Funksiya adı gözlənilirdi")
        self._expect(T.LPAREN, "'(' gözlənilirdi")
        params = self._parse_params()
        self._expect(T.RPAREN, "')' gözlənilirdi")
        body = self._parse_block()
        return A.FunctionDef(
            line=tok.line, name=str(name_tok.value), params=params, body=body
        )

    def _parse_params(self) -> List[A.Param]:
        params: List[A.Param] = []
        if self._check(T.RPAREN):
            return params
        seen_default = False
        while True:
            name_tok = self._expect(T.IDENT, "Parametr adı gözlənilirdi")
            default: Optional[A.Node] = None
            if self._match(T.ASSIGN):
                default = self._parse_expr()
                seen_default = True
            else:
                if seen_default:
                    raise self._err(
                        "Default qiymətsiz parametr default qiymətli parametrdən sonra gələ bilməz",
                        name_tok,
                    )
            params.append(A.Param(line=name_tok.line, name=str(name_tok.value), default=default))
            if not self._match(T.COMMA):
                break
        return params

    def _parse_class_def(self) -> A.ClassDef:
        tok = self._expect(T.CLASS)
        name_tok = self._expect(T.IDENT, "Sinif adı gözlənilirdi")
        bases: List[A.Node] = []
        if self._match(T.LPAREN):
            if not self._check(T.RPAREN):
                while True:
                    bases.append(self._parse_expr())
                    if not self._match(T.COMMA):
                        break
            self._expect(T.RPAREN, "')' gözlənilirdi")
        body = self._parse_block()
        return A.ClassDef(
            line=tok.line, name=str(name_tok.value), bases=bases, body=body
        )

    def _parse_try(self) -> A.Try:
        tok = self._expect(T.TRY)
        body = self._parse_block()
        catches: List[A.CatchClause] = []
        finally_body: List[A.Node] = []
        while True:
            saved = self.pos
            self._skip_newlines()
            if self._check(T.CATCH):
                self._match(T.CATCH)
                var: Optional[str] = None
                if self._check(T.IDENT):
                    var = str(self._match(T.IDENT).value)
                cb = self._parse_block()
                catches.append(A.CatchClause(line=tok.line, var=var, body=cb))
                continue
            if self._check(T.FINALLY):
                self._match(T.FINALLY)
                finally_body = self._parse_block()
                break
            self.pos = saved
            break
        if not catches and not finally_body:
            raise self._err("'try' ən azı bir 'catch' və ya 'finally' tələb edir", tok)
        return A.Try(line=tok.line, body=body, catches=catches, finally_body=finally_body)

    def _parse_import(self) -> A.Import:
        tok = self._expect(T.IMPORT)
        if self._check(T.STRING):
            s = self._match(T.STRING)
            target = str(s.value)
            is_path = True
        elif self._check(T.IDENT):
            i = self._match(T.IDENT)
            target = str(i.value)
            is_path = False
        else:
            raise self._err("Modul adı və ya yolu (string) gözlənilirdi")
        alias: Optional[str] = None
        if self._match(T.AS):
            a = self._expect(T.IDENT, "alias adı gözlənilirdi")
            alias = str(a.value)
        return A.Import(line=tok.line, target=target, alias=alias, is_path=is_path)

    def _parse_return(self) -> A.Return:
        tok = self._expect(T.RETURN)
        value: Optional[A.Node] = None
        if not self._check(T.NEWLINE) and not self._check(T.EOF) and not self._check(T.DEDENT):
            value = self._parse_expr()
        self._consume_end_of_stmt()
        return A.Return(line=tok.line, value=value)

    def _parse_throw(self) -> A.Throw:
        tok = self._expect(T.THROW)
        value = self._parse_expr()
        self._consume_end_of_stmt()
        return A.Throw(line=tok.line, value=value)

    def _parse_expr_or_assign(self) -> A.Node:
        tok = self._peek()
        expr = self._parse_expr()

        # augmented assignment
        aug_map = {
            T.PLUS_EQ: "+=",
            T.MINUS_EQ: "-=",
            T.STAR_EQ: "*=",
            T.SLASH_EQ: "/=",
            T.PERCENT_EQ: "%=",
        }
        for tt, op in aug_map.items():
            if self._check(tt):
                self._match(tt)
                value = self._parse_expr()
                self._consume_end_of_stmt()
                return A.AugAssign(line=tok.line, target=expr, op=op, value=value)

        # plain assignment (chained: a = b = c)
        if self._check(T.ASSIGN):
            targets: List[A.Node] = [expr]
            while self._match(T.ASSIGN):
                next_expr = self._parse_expr()
                # Davamlı '=' varsa, sonuncusu dəyər olur
                if self._check(T.ASSIGN):
                    targets.append(next_expr)
                else:
                    self._consume_end_of_stmt()
                    return A.Assign(line=tok.line, targets=targets, value=next_expr)
            # buraya çatmamalıyıq
        self._consume_end_of_stmt()
        return A.ExpressionStmt(line=tok.line, expr=expr)

    # ---------- ifadələr (expressions) ----------
    def _parse_expr(self) -> A.Node:
        if self._check(T.LAMBDA):
            return self._parse_lambda()
        return self._parse_or()

    def _parse_lambda(self) -> A.Node:
        tok = self._expect(T.LAMBDA)
        params: List[str] = []
        if not self._check(T.COLON):
            while True:
                ident = self._expect(T.IDENT, "lambda parametri gözlənilirdi")
                params.append(str(ident.value))
                if not self._match(T.COMMA):
                    break
        self._expect(T.COLON, "':' gözlənilirdi")
        body = self._parse_expr()
        return A.Lambda(line=tok.line, params=params, body=body)

    def _parse_or(self) -> A.Node:
        left = self._parse_and()
        while self._check(T.OR):
            tok = self._match(T.OR)
            right = self._parse_and()
            left = A.LogicalOp(line=tok.line, op="or", left=left, right=right)
        return left

    def _parse_and(self) -> A.Node:
        left = self._parse_not()
        while self._check(T.AND):
            tok = self._match(T.AND)
            right = self._parse_not()
            left = A.LogicalOp(line=tok.line, op="and", left=left, right=right)
        return left

    def _parse_not(self) -> A.Node:
        if self._check(T.NOT):
            tok = self._match(T.NOT)
            operand = self._parse_not()
            return A.UnaryOp(line=tok.line, op="not", operand=operand)
        return self._parse_compare()

    _CMP = {
        T.EQ: "==",
        T.NEQ: "!=",
        T.LT: "<",
        T.GT: ">",
        T.LEQ: "<=",
        T.GEQ: ">=",
    }

    def _parse_compare(self) -> A.Node:
        left = self._parse_addition()
        ops: List[str] = []
        comps: List[A.Node] = []
        while self._peek().type in self._CMP or self._check(T.IN) or (
            self._check(T.NOT) and self._peek(1).type == T.IN
        ):
            tok = self._peek()
            if tok.type in self._CMP:
                self.pos += 1
                ops.append(self._CMP[tok.type])
            elif self._check(T.IN):
                self._match(T.IN)
                ops.append("in")
            elif self._check(T.NOT) and self._peek(1).type == T.IN:
                self._match(T.NOT)
                self._match(T.IN)
                ops.append("not in")
            comps.append(self._parse_addition())
        if not ops:
            return left
        return A.Compare(line=left.line, left=left, ops=ops, comparators=comps)

    def _parse_addition(self) -> A.Node:
        left = self._parse_multiplication()
        while self._check(T.PLUS, T.MINUS):
            tok = self._peek()
            self.pos += 1
            op = "+" if tok.type == T.PLUS else "-"
            right = self._parse_multiplication()
            left = A.BinaryOp(line=tok.line, op=op, left=left, right=right)
        return left

    def _parse_multiplication(self) -> A.Node:
        left = self._parse_unary()
        while self._check(T.STAR, T.SLASH, T.DSLASH, T.PERCENT):
            tok = self._peek()
            self.pos += 1
            op = {
                T.STAR: "*",
                T.SLASH: "/",
                T.DSLASH: "//",
                T.PERCENT: "%",
            }[tok.type]
            right = self._parse_unary()
            left = A.BinaryOp(line=tok.line, op=op, left=left, right=right)
        return left

    def _parse_unary(self) -> A.Node:
        if self._check(T.MINUS, T.PLUS):
            tok = self._peek()
            self.pos += 1
            op = "-" if tok.type == T.MINUS else "+"
            operand = self._parse_unary()
            return A.UnaryOp(line=tok.line, op=op, operand=operand)
        return self._parse_power()

    def _parse_power(self) -> A.Node:
        base = self._parse_call_expr()
        if self._check(T.DSTAR):
            tok = self._match(T.DSTAR)
            exp = self._parse_unary()  # right associative
            return A.BinaryOp(line=tok.line, op="**", left=base, right=exp)
        return base

    def _parse_call_expr(self) -> A.Node:
        node = self._parse_primary()
        while True:
            if self._check(T.LPAREN):
                self._match(T.LPAREN)
                args, kwargs = self._parse_call_args()
                rp = self._expect(T.RPAREN, "')' gözlənilirdi")
                node = A.Call(line=node.line, func=node, args=args, kwargs=kwargs)
            elif self._check(T.DOT):
                self._match(T.DOT)
                name_tok = self._expect(T.IDENT, "Atribut adı gözlənilirdi")
                node = A.Attribute(line=node.line, obj=node, name=str(name_tok.value))
            elif self._check(T.LBRACK):
                self._match(T.LBRACK)
                idx = self._parse_subscript_index()
                self._expect(T.RBRACK, "']' gözlənilirdi")
                node = A.Subscript(line=node.line, obj=node, index=idx)
            else:
                break
        return node

    def _parse_subscript_index(self) -> A.Node:
        # Ya tək index, ya slice (a:b:c)
        line = self._peek().line
        start: Optional[A.Node] = None
        stop: Optional[A.Node] = None
        step: Optional[A.Node] = None
        is_slice = False
        if not self._check(T.COLON):
            start = self._parse_expr()
        if self._match(T.COLON):
            is_slice = True
            if not self._check(T.COLON) and not self._check(T.RBRACK):
                stop = self._parse_expr()
            if self._match(T.COLON):
                if not self._check(T.RBRACK):
                    step = self._parse_expr()
        if is_slice:
            return A.Slice(line=line, start=start, stop=stop, step=step)
        assert start is not None
        return start

    def _parse_call_args(self) -> Tuple[List[A.Node], List[Tuple[str, A.Node]]]:
        args: List[A.Node] = []
        kwargs: List[Tuple[str, A.Node]] = []
        if self._check(T.RPAREN):
            return args, kwargs
        while True:
            # keyword arg: IDENT '=' expr
            if self._check(T.IDENT) and self._peek(1).type == T.ASSIGN:
                name_tok = self._match(T.IDENT)
                self._match(T.ASSIGN)
                value = self._parse_expr()
                kwargs.append((str(name_tok.value), value))
            else:
                args.append(self._parse_expr())
            if not self._match(T.COMMA):
                break
        return args, kwargs

    def _parse_primary(self) -> A.Node:
        tok = self._peek()
        t = tok.type
        if t == T.NUMBER:
            self.pos += 1
            return A.NumberLit(line=tok.line, value=tok.value)
        if t == T.STRING:
            self.pos += 1
            return A.StringLit(line=tok.line, value=str(tok.value))
        if t == T.TRUE:
            self.pos += 1
            return A.BoolLit(line=tok.line, value=True)
        if t == T.FALSE:
            self.pos += 1
            return A.BoolLit(line=tok.line, value=False)
        if t == T.NONE:
            self.pos += 1
            return A.NoneLit(line=tok.line)
        if t == T.IDENT:
            self.pos += 1
            return A.Identifier(line=tok.line, name=str(tok.value))
        if t == T.LPAREN:
            self.pos += 1
            node = self._parse_expr()
            self._expect(T.RPAREN, "')' gözlənilirdi")
            return node
        if t == T.LBRACK:
            return self._parse_list_literal()
        if t == T.LBRACE:
            return self._parse_dict_literal()
        raise self._err(f"Gözlənilməz token: {tok.type.name} ({tok.value!r})", tok)

    def _parse_list_literal(self) -> A.ListLit:
        tok = self._expect(T.LBRACK)
        elements: List[A.Node] = []
        if not self._check(T.RBRACK):
            while True:
                elements.append(self._parse_expr())
                if not self._match(T.COMMA):
                    break
        self._expect(T.RBRACK, "']' gözlənilirdi")
        return A.ListLit(line=tok.line, elements=elements)

    def _parse_dict_literal(self) -> A.DictLit:
        tok = self._expect(T.LBRACE)
        pairs: List[Tuple[A.Node, A.Node]] = []
        if not self._check(T.RBRACE):
            while True:
                k = self._parse_expr()
                self._expect(T.COLON, "':' gözlənilirdi (dict)")
                v = self._parse_expr()
                pairs.append((k, v))
                if not self._match(T.COMMA):
                    break
        self._expect(T.RBRACE, "'}' gözlənilirdi")
        return A.DictLit(line=tok.line, pairs=pairs)


def parse(tokens: List[Token], filename: Optional[str] = None) -> A.Program:
    return Parser(tokens, filename=filename).parse()

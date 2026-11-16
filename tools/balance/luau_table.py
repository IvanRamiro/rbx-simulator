"""A small reader for the Luau table literals the game keeps its tuning in (GameConfig.lua, PetRules.Sizes, Bridges.lua).

It understands what those files use: tables (array and keyed parts), numbers, strings, true/false/nil, comments, simple
arithmetic (0.85 / 0.55), and constructor calls such as Color3.fromRGB(...), Vector3.new(...) or Enum.KeyCode.E, which
come back as ("call", "Vector3.new", [args]) or ("name", "Enum.KeyCode.E"). Nothing is executed.

    read_table(text, start_marker)   the table literal that starts at the first "{" after start_marker
"""

import re

_TOKEN = re.compile(
    r"""
    (?P<space>\s+)
  | (?P<comment>--\[(?P<eq>=*)\[.*?\](?P=eq)\]|--[^\n]*)
  | (?P<number>0[xX][0-9a-fA-F]+|\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)
  | (?P<string>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)
  | (?P<op>[{}\[\]()=,;*/+\-#])
    """,
    re.S | re.X,
)


def _tokens(text):
    position = 0
    while position < len(text):
        match = _TOKEN.match(text, position)
        if not match:
            raise ValueError("Unreadable Luau near: " + text[position:position + 60])
        position = match.end()
        kind = match.lastgroup
        if kind in ("space", "comment", "eq"):
            continue
        if match.group("comment") is not None:
            continue
        yield kind, match.group(kind)


class _Parser:
    def __init__(self, text):
        self.stream = _tokens(text)  # read lazily: what follows the table may be code this reader doesn't know
        self.tokens = []
        self.at = 0

    def peek(self, offset=0):
        index = self.at + offset
        while len(self.tokens) <= index:
            token = next(self.stream, None)
            if token is None:
                return (None, None)
            self.tokens.append(token)
        return self.tokens[index]

    def take(self, value=None):
        token = self.peek()
        if value is not None and token[1] != value:
            raise ValueError("Expected %r, found %r" % (value, token[1]))
        self.at += 1
        return token

    def table(self):
        self.take("{")
        array, keyed = [], {}
        while self.peek()[1] != "}":
            kind, value = self.peek()
            if kind == "name" and self.peek(1)[1] == "=" and "." not in value:
                self.take()
                self.take("=")
                keyed[value] = self.expression()
            elif value == "[":
                self.take("[")
                key = self.expression()
                self.take("]")
                self.take("=")
                keyed[key] = self.expression()
            else:
                array.append(self.expression())
            if self.peek()[1] in (",", ";"):
                self.take()
        self.take("}")
        if keyed and array:
            keyed["__array"] = array
            return keyed
        return keyed if keyed else array

    def expression(self):
        value = self.term()
        while self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            right = self.term()
            value = value + right if op == "+" else value - right
        return value

    def term(self):
        value = self.unary()
        while self.peek()[1] in ("*", "/"):
            op = self.take()[1]
            right = self.unary()
            value = value * right if op == "*" else value / right
        return value

    def unary(self):
        if self.peek()[1] == "-":
            self.take()
            return -self.unary()
        return self.atom()

    def atom(self):
        kind, value = self.peek()
        if value == "{":
            return self.table()
        if value == "(":
            self.take()
            inner = self.expression()
            self.take(")")
            return inner
        self.take()
        if kind == "number":
            return int(value, 16) if value.lower().startswith("0x") else (float(value) if re.search(r"[.eE]", value) else int(value))
        if kind == "string":
            return bytes(value[1:-1], "utf-8").decode("unicode_escape")
        if kind == "name":
            if value == "true":
                return True
            if value == "false":
                return False
            if value == "nil":
                return None
            if self.peek()[1] == "(":
                self.take("(")
                args = []
                while self.peek()[1] != ")":
                    args.append(self.expression())
                    if self.peek()[1] == ",":
                        self.take()
                self.take(")")
                return ("call", value, args)
            return ("name", value)
        raise ValueError("Unexpected token %r" % (value,))


def read_table(text, start_marker):
    start = text.index(start_marker)
    brace = text.index("{", start)
    parser = _Parser(text[brace:])
    return parser.table()

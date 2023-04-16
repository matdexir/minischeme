import math
import operator as op
from typing import Union

Symbol = str
Number = Union[int, float]
Atom = Union[Symbol, Number]
List = list
Exp = Union[Atom, List]
Env = dict


def standard_env() -> Env:
    # defining an environment with some scheme standards
    env = Env()
    env.update(vars(math))
    env.update(
        {
            "+": op.add,
            "-": op.sub,
            "*": op.mul,
            "/": op.truediv,
            ">": op.gt,
            "<": op.lt,
            ">=": op.ge,
            "<=": op.le,
            "=": op.eq,
            "abs": abs,
            "append": op.add,
            "apply": lambda proc, args: proc(*args),
            "begin": lambda *x: x[-1],
            "car": lambda x: x[0],
            "cdr": lambda x: x[1:],
            "cons": lambda x, y: [x] + y,
            "eq?": op.is_,
            "expt": pow,
            "equal?": op.eq,
            "length": len,
            "list": lambda *x: List(x),
            "list?": lambda x: isinstance(x, List),
            "map": map,
            "max": max,
            "min": min,
            "not": op.not_,
            "null?": lambda x: x == [],
            "number?": lambda x: isinstance(x, Number),
            "print": print,
            "procedure?": callable,
            "round": round,
            "symbol?": lambda x: isinstance(x, Symbol),
        }
    )
    return env


def tokenize(chars: str) -> list:
    # converts a string of characters into a list of tokens
    return chars.replace("(", " ( ").replace(")", " ) ").split()


def parse(program: str) -> Exp:
    # reads a scheme expression from a string
    return read_from_tokens(tokenize(program))


def read_from_tokens(tokens: list) -> Exp:
    # read an expression from a sequence of tokens
    if len(tokens) == 0:
        raise SyntaxError("unexpected EOF")
    token = tokens.pop(0)
    if token == "(":
        L = []
        while tokens[0] != ")":
            L.append(read_from_tokens(tokens))
        tokens.pop(0)  # pop of #
        return L
    elif token == ")":
        raise SyntaxError("unexpected )")
    else:
        return atom(token)


def atom(token: str) -> Atom:
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)

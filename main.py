import math
import operator as op
from typing import Union

Symbol = str
Number = Union[int, float]
Atom = Union[Symbol, Number]
List = list
Exp = Union[Atom, List]


class Env(dict):
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms, args))
        self.outer = outer

    def find(self, var):
        return self if (var in self) else self.outer.find(var)


class Procedure(object):
    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env

    def __call__(self, *args):
        return eval(self.body, Env(self.parms, args, self.env))


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


global_env = standard_env()


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
        tokens.pop(0)  # pop of )
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


def eval(x: Exp, env=global_env):
    # evaluate an expression in an env
    if isinstance(x, Symbol):  # ref to variable
        return env.find(x)[x]
    elif not isinstance(x, List):  # constant
        return x
    op, *args = x
    if op == "quote":
        return args[0]
    elif op == "if":
        (test, conseq, alt) = args
        exp = conseq if eval(test, env) else alt
        return eval(exp, env)
    elif op == "define":
        (symbol, exp) = args
        env[symbol] = eval(exp, env)
    elif op == "set!":
        (symbol, exp) = args
        env.find(symbol)[symbol] = eval(exp, env)
    elif op == "lambda":
        (parms, body) = args
        return Procedure(parms, body, env)
    else:
        proc = eval(op, env)
        vals = [eval(arg, env) for arg in args]
        return proc(*vals)


def repl(prompt="minischeme> "):
    while True:
        val = parse(input(prompt))
        print(val)
        val = eval(val)
        if val is not None:
            print(schemestr(val))


def schemestr(exp) -> str:
    if isinstance(exp, List):
        return "(" + " ".join(map(schemestr, exp)) + ")"
    else:
        return str(exp)


if __name__ == "__main__":
    repl()

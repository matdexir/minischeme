import atexit
import cmath
import math
import operator as op
import os
import pprint
import re
import readline as rl
import sys
from typing import Union

histfile = os.path.join(os.path.expanduser("."), ".mscm_histfile")
rl.parse_and_bind("set editing-mode vi")


try:
    rl.read_history_file(histfile)
except FileNotFoundError:
    os.mknod(histfile)


isa = isinstance


class Symbol(str):
    pass


def Sym(s, symbol_table={}):
    if s not in symbol_table:
        symbol_table[s] = Symbol(s)
    return symbol_table[s]


_quote, _if, _set, _define, _lambda, _begin, _definemacro = map(
    Sym, "quote if set! define lambda begin define-macro".split()
)

_quasiquote, _unquote, _unquotesplicing = map(
    Sym, "quasiquote unquote unquote-splicing".split()
)

eof_object = Symbol("#<eof-object>")


def readchar(inport):
    "Read the next character from an input port."
    if inport.line != "":
        ch, inport.line = input.line[0], inport.line[1:]
        return ch
    else:
        return inport.file.read(1) or eof_object


def read(inport):
    "Read a Scheme expression from an input port"

    def read_ahead(token):
        if "(" == token:
            L = []
            while True:
                token = inport.next_token()
                if token == ")":
                    return L
                else:
                    L.append(read_ahead(token))
        elif ")" == token:
            raise SyntaxError("unexpected )")
        elif token in quotes:
            return [quotes[token], read(inport)]
        elif token is eof_object:
            raise SyntaxError("unexpected EOF in list")
        else:
            return atom(token)


quotes = {"'": _quote, "`": _quasiquote, ",": _unquote, ",@": _unquotesplicing}


def atom(token):
    "Numbers become numbers; #t and #f are boolean; '...' string; otherwise Symbol"
    if token == "#t":
        return True
    elif token == "#f":
        return False
    elif token[0] == '"':
        return token[1:-1].decode("string_escape")
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            try:
                return complex(token.replace("i", "j", 1))
            except ValueError:
                return Sym(token)


def to_string(x):
    "Convert a Python object back into a Lisp-readable string."
    if x is True:
        return "#t"
    elif x is False:
        return "#f"
    elif isa(x, Symbol):
        return x
    elif isa(x, str):
        x = x.encode("string_escape").replace('"', r"\"")
        return f"{x}"
    elif isa(x, list):
        return "(" + " ".join(map(to_string, x)) + ")"
    elif isa(x, complex):
        return str(x).replace("j", "i")
    else:
        return str(x)


def load(filename):
    "Eval every expression from a file"
    repl(None, InPort(open(filename)), None)


def repl(prompt="minischeme> ", inport=InPort(sys.stdin), out=sys.stdout):
    "A prompt read-eval-print loop"
    sys.stderr.write("minischeme 2.0\n")
    while True:
        try:
            if prompt:
                sys.stderr.write(prompt)
            x = parse(inport)
            if x is eof_object:
                return
            val = eval(x)
            if val is not None and out:
                print(to_string(val), file=out)
        except Exception as e:
            print(f"{type(e).__name__}: {e}")


class InPort(object):
    "An input port. Retains a line of chars"
    tokenizer = r"""\s*(,@|[('`,)]|"(?:[\\].|[^\\"])*"|;.*|[^\s('"`,;)]*)(.*)"""

    def __init__(self, file) -> None:
        self.file = file
        self.line = ""

    def next_token(self):
        "returns the next token, reading new text into line buffer if needed"
        while True:
            if self.line == "":
                self.line = self.file.readline()
            if self.line == "":
                return eof_object
            token, self.line = re.match(InPort.tokenizer, self.line).groups()
            if token != "" and not token.startswith(";"):
                return token


Number = Union[int, float]
Atom = Union[Symbol, Number]
List = list
Exp = Union[Atom, List]


class Env(dict):
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms, args))
        self.outer = outer

    def find(self, var):
        pprint.pprint(self.keys())
        if var in self:
            return self
        if self.outer:
            return self.outer.find(var)
        # return self if (var in self) else self.outer.find(var)


class Procedure(object):
    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env

    def __call__(self, *args):
        return eval(self.body, Env(self.parms, args, self.env))


def standard_env() -> Env:
    # defining an environment with some scheme standards
    env = Env()
    env.update(vars(math))
    env.update(vars(cmath))
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


def tokenize(chars: str):
    # converts a string of characters into a list of tokens
    return chars.replace("(", " ( ").replace(")", " ) ").split()


def parse(program: str):
    # reads a scheme expression from a string
    return read_from_tokens(tokenize(program))


def read_from_tokens(tokens: list):
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


def eval(x, env=global_env):
    # evaluate an expression in an env
    while True:
        if isa(x, Symbol):  # variable reference
            return env.find(x)[x]
        elif not isa(x, list):  # constant literal
            return x
        elif x[0] is _quote:  # (quote exp)
            (_, exp) = x
            return exp
        elif x[0] is _if:  # (if test conseq alt)
            (_, test, conseq, alt) = x
            x = conseq if eval(test, env) else alt
        elif x[0] is _set:  # (set! var exp)
            (_, var, exp) = x
            env.find(var)[var] = eval(exp, env)
            return None
        elif x[0] is _define:  # (define var exp)
            (_, var, exp) = x
            env[var] = eval(exp, env)
            return None
        elif x[0] is _lambda:  # (lambda (var*) exp)
            (_, vars, exp) = x
            return Procedure(vars, exp, env)
        elif x[0] is _begin:  # (begin exp+)
            for exp in x[1:-1]:
                eval(exp, env)
            x = x[-1]
        else:  # (proc exp*)
            exps = [eval(exp, env) for exp in x]
            proc = exps.pop(0)
            if isa(proc, Procedure):
                x = proc.exp
                env = Env(proc.parms, exps, proc.env)
            else:
                return proc(*exps)


def schemestr(exp) -> str:
    if isinstance(exp, List):
        return "(" + " ".join(map(schemestr, exp)) + ")"
    else:
        return str(exp)


@atexit.register
def goodbye_msg():
    print("Goodbye!")


if __name__ == "__main__":
    repl()

atexit.register(rl.write_history_file, histfile)

from typing import Union

Symbol = str
Number = Union[int, float]
Atom = Union[Symbol, Number]
List = list
Exp = Union[Atom, List]
Env = dict


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

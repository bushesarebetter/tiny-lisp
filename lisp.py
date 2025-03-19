import math
import operator as op
import re
import sys


class LispError(Exception):
    pass


class Incomplete(LispError):  # input ended mid-expression; the REPL reads another line
    pass


class Symbol(str):
    pass


QUOTE, IF, DEFINE, LAMBDA, LET, BEGIN, SET = map(Symbol, ['quote', 'if', 'define', 'lambda', 'let', 'begin', 'set!'])

TOKEN = re.compile(r'''\s+|;[^\n]*|("(?:\\.|[^"\\])*"|[()']|[^\s()'";]+)''')
INT = re.compile(r'[+-]?\d+')
FLOAT = re.compile(r'[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?')


def tokenize(src):
    tokens, pos = [], 0
    while pos < len(src):
        m = TOKEN.match(src, pos)
        if not m:
            raise Incomplete('unterminated string') if src[pos] == '"' else LispError(f'bad character {src[pos]!r}')
        if m.group(1):
            tokens.append(m.group(1))
        pos = m.end()
    return tokens


def atom(tok):
    if tok[0] == '"':
        return re.sub(r'\\(.)', lambda m: {'n': '\n', 't': '\t'}.get(m[1], m[1]), tok[1:-1])
    if tok == '#t':
        return True
    if tok == '#f':
        return False
    if INT.fullmatch(tok):
        return int(tok)
    if FLOAT.fullmatch(tok):
        return float(tok)
    return Symbol(tok)


def read_all(src):
    tokens, pos = tokenize(src), 0

    def read():
        nonlocal pos
        if pos == len(tokens):
            raise Incomplete('unexpected end of input')
        tok = tokens[pos]
        pos += 1
        if tok == '(':
            items = []
            while True:
                if pos == len(tokens):
                    raise Incomplete('missing )')
                if tokens[pos] == ')':
                    pos += 1
                    return items
                items.append(read())
        if tok == ')':
            raise LispError('unexpected )')
        if tok == "'":
            return [QUOTE, read()]
        return atom(tok)

    exprs = []
    while pos < len(tokens):
        exprs.append(read())
    return exprs


class Env(dict):
    def __init__(self, bindings=(), outer=None):
        super().__init__(bindings)
        self.outer = outer

    def find(self, name):
        env = self
        while env is not None:
            if name in env:
                return env
            env = env.outer
        raise LispError(f'unbound symbol: {name}')


class Procedure:
    def __init__(self, params, body, env):
        if not isinstance(params, list) or not all(isinstance(p, Symbol) for p in params):
            raise LispError('lambda parameters must be a list of symbols')
        if not body:
            raise LispError('lambda needs a body')
        self.params, self.env = params, env
        self.body = body[0] if len(body) == 1 else [BEGIN, *body]

    def bind(self, args):
        if len(args) != len(self.params):
            raise LispError(f'expected {len(self.params)} arguments, got {len(args)}')
        return Env(zip(self.params, args), self.env)

    def __call__(self, *args):
        return evaluate(self.body, self.bind(args))


def check(ok, form):
    if not ok:
        raise LispError(f'bad syntax in {form}')


def evaluate(x, env):
    # Tail positions (if branches, last expr of begin/let/body, procedure calls)
    # rebind x/env and loop instead of recursing, so tail calls use no Python stack.
    while True:
        if isinstance(x, Symbol):
            return env.find(x)[x]
        if not isinstance(x, list):
            return x
        if not x:
            raise LispError('cannot evaluate ()')
        head, args = x[0], x[1:]
        kw = head if isinstance(head, Symbol) else None  # a string "if" is not the keyword
        if kw == QUOTE:
            check(len(args) == 1, 'quote')
            return args[0]
        if kw == IF:
            check(len(args) in (2, 3), 'if')
            if evaluate(args[0], env) is not False:
                x = args[1]
            elif len(args) == 3:
                x = args[2]
            else:
                return None
            continue
        if kw == DEFINE:
            check(len(args) >= 2, 'define')
            target = args[0]
            if isinstance(target, list):
                check(target and isinstance(target[0], Symbol), 'define')
                env[target[0]] = Procedure(target[1:], args[1:], env)
            else:
                check(isinstance(target, Symbol) and len(args) == 2, 'define')
                env[target] = evaluate(args[1], env)
            return None
        if kw == SET:
            check(len(args) == 2 and isinstance(args[0], Symbol), 'set!')
            env.find(args[0])[args[0]] = evaluate(args[1], env)
            return None
        if kw == LAMBDA:
            check(len(args) >= 1, 'lambda')
            return Procedure(args[0], args[1:], env)
        if kw == BEGIN:
            if not args:
                return None
            for e in args[:-1]:
                evaluate(e, env)
            x = args[-1]
            continue
        if kw == LET:
            check(len(args) >= 2 and isinstance(args[0], list), 'let')
            for b in args[0]:
                check(isinstance(b, list) and len(b) == 2 and isinstance(b[0], Symbol), 'let')
            env = Env({name: evaluate(val, env) for name, val in args[0]}, env)
            x = args[1] if len(args) == 2 else [BEGIN, *args[1:]]
            continue

        proc = evaluate(head, env)
        vals = [evaluate(a, env) for a in args]
        if isinstance(proc, Procedure):
            env, x = proc.bind(vals), proc.body
            continue
        if not callable(proc):
            raise LispError(f'not a procedure: {to_str(proc)}')
        return proc(*vals)


def to_str(x, display=False):
    if x is True:
        return '#t'
    if x is False:
        return '#f'
    if isinstance(x, Symbol):
        return x
    if isinstance(x, str):
        return x if display else '"' + x.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if isinstance(x, list):
        return '(' + ' '.join(to_str(e, display) for e in x) + ')'
    if callable(x):
        return '#<procedure>'
    return str(x)


def chain(f):
    return lambda *xs: all(f(a, b) for a, b in zip(xs, xs[1:]))


def div(a, *rest):
    for b in rest:
        if b == 0:
            raise LispError('division by zero')
        a = a // b if isinstance(a, int) and isinstance(b, int) and a % b == 0 else a / b
    return a


def car(xs):
    if not isinstance(xs, list) or not xs:
        raise LispError(f'car: expected a non-empty list, got {to_str(xs)}')
    return xs[0]


def cdr(xs):
    if not isinstance(xs, list) or not xs:
        raise LispError(f'cdr: expected a non-empty list, got {to_str(xs)}')
    return xs[1:]


def cons(a, b):
    if not isinstance(b, list):
        raise LispError('cons: second argument must be a list (no dotted pairs)')
    return [a, *b]


def display(x):
    sys.stdout.write(to_str(x, display=True))


def standard_env():
    return Env({
        '+': lambda *xs: sum(xs), '*': lambda *xs: math.prod(xs),
        '-': lambda a, *rest: a - sum(rest) if rest else -a, '/': div,
        'modulo': op.mod, 'abs': abs, 'min': min, 'max': max,
        '=': chain(op.eq), '<': chain(op.lt), '>': chain(op.gt), '<=': chain(op.le), '>=': chain(op.ge),
        'not': lambda x: x is False,
        'car': car, 'cdr': cdr, 'cons': cons, 'list': lambda *xs: list(xs),
        'length': len, 'null?': lambda x: isinstance(x, list) and not x,
        'pair?': lambda x: isinstance(x, list) and x != [],
        'number?': lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
        'symbol?': lambda x: isinstance(x, Symbol), 'procedure?': callable,
        'eq?': lambda a, b: a is b or (not isinstance(a, list) and a == b), 'equal?': op.eq,
        'display': display, 'newline': lambda: print(),
    })


def run(src, env):
    result = None
    for x in read_all(src):
        result = evaluate(x, env)
    return result







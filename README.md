# Tiny Lisp

A small Scheme-like interpreter in about 300 lines of Python. Tail calls run in a loop instead of recursing, so a tail-recursive function can go a million calls deep without touching Python's recursion limit.

It supports `define`, `lambda`, `if`, `let`, `begin`, `quote` (and `'x`), `set!`, closures with lexical scope, ints, floats, strings, `#t`/`#f`, and a handful of list and arithmetic builtins. Lists are Python lists, so there are no dotted pairs.

[Setup](#setup) · [Run](#run) · [Examples](#examples) · [Tests](#test)

## Setup

Python 3.10+ and nothing else. You only need `pytest` if you want to run the tests.

## Run

```bash
python lisp.py examples.scm   # run a file
python lisp.py                # REPL; multi-line input works, Ctrl-D/Ctrl-Z to quit
```

## Examples

`examples.scm` has factorial, naive and iterative fib, `map`/`filter`/`range` written in lisp, a closure counter, and a million-deep tail-recursive countdown:

```text
(fact 20)      => 2432902008176640000
(fib 20)       => 6765
(fib-iter 100) => 354224848179261915075
squares        => (1 4 9 16 25 36 49 64 81 100)
evens          => (2 4 6 8 10 12 14 16 18 20)
c1 after 3     => 3
c2 after 1     => 1
(count-down 1000000) => done
```

Calls that aren't in tail position, like the one in `fact`, still use the Python stack. The script raises the recursion limit to 20000 for those.

## Test

Install the test dependency:

```bash
pip install pytest
```

```bash
python -m pytest -q
```

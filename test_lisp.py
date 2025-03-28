from pathlib import Path

import pytest

from lisp import LispError, read_all, run, standard_env


def ev(src):
    return run(src, standard_env())


def test_arithmetic():
    assert ev('(+ 1 2 (* 3 4))') == 15
    assert ev('(- 10 4 1)') == 5
    assert ev('(- 5)') == -5
    assert ev('(/ 8 2)') == 4
    assert ev('(/ 7 2)') == 3.5
    assert ev('(* 1.5 2)') == 3.0
    assert ev('(< 1 2 3)') is True
    assert ev('(= 1 2)') is False


def test_special_forms():
    assert ev("'(a (b 1))") == ['a', ['b', 1]]
    assert ev('(if #f 1 2)') == 2
    assert ev('(if 0 1 2)') == 1  # only #f is false
    assert ev('(let ((x 2) (y 3)) (* x y))') == 6
    assert ev('(begin (define x 1) (set! x (+ x 41)) x)') == 42


def test_closures_and_lexical_scope():
    assert ev('''
        (define (make-counter) (let ((n 0)) (lambda () (set! n (+ n 1)) n)))
        (define a (make-counter))
        (define b (make-counter))
        (a) (a) (b)
        (list (a) (b))''') == [3, 2]
    assert ev('(define x 1) (define (f) x) (let ((x 2)) (f))') == 1
    assert ev('(define (adder n) (lambda (x) (+ x n))) ((adder 10) 5)') == 15


def test_recursion():
    assert ev('(define (fact n) (if (= n 0) 1 (* n (fact (- n 1))))) (fact 20)') == 2432902008176640000
    assert ev('''
        (define (map f xs) (if (null? xs) '() (cons (f (car xs)) (map f (cdr xs)))))
        (map (lambda (x) (* x x)) '(1 2 3))''') == [1, 4, 9]


def test_deep_tail_recursion():
    # Python's default recursion limit is 1000, so this only works with real tail calls.
    assert ev('(define (loop n acc) (if (= n 0) acc (loop (- n 1) (+ acc 1)))) (loop 100000 0)') == 100000
    assert ev('''
        (define (even? n) (if (= n 0) #t (odd? (- n 1))))
        (define (odd? n) (if (= n 0) #f (even? (- n 1))))
        (even? 100001)''') is False


def test_errors():
    with pytest.raises(LispError, match='unbound symbol: nope'):
        ev('(+ 1 nope)')
    with pytest.raises(LispError, match='unbound symbol: y'):
        ev('(set! y 1)')
    with pytest.raises(LispError, match='expected 1 arguments, got 2'):
        ev('((lambda (x) x) 1 2)')
    with pytest.raises(LispError, match='not a procedure'):
        ev('(1 2)')
    with pytest.raises(LispError):
        read_all('(+ 1 2')
    with pytest.raises(LispError):
        read_all(')')


def test_examples_file(capsys):
    run((Path(__file__).parent / 'examples.scm').read_text(), standard_env())
    out = capsys.readouterr().out
    assert '(fib 20)       => 6765' in out
    assert 'c1 after 3     => 3' in out
    assert '(count-down 1000000) => done' in out

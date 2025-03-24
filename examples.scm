; Run with: python lisp.py examples.scm

(define (show label value)
  (display label) (display value) (newline))

; factorial (plain recursion)
(define (fact n)
  (if (= n 0) 1 (* n (fact (- n 1)))))
(show "(fact 20)      => " (fact 20))

; fibonacci: naive tree recursion, and an iterative version with an inner define
(define (fib n)
  (if (< n 2) n (+ (fib (- n 1)) (fib (- n 2)))))
(define (fib-iter n)
  (define (go a b k)
    (if (= k 0) a (go b (+ a b) (- k 1))))
  (go 0 1 n))
(show "(fib 20)       => " (fib 20))
(show "(fib-iter 100) => " (fib-iter 100))

; map / filter / range written in lisp
(define (map f xs)
  (if (null? xs) '() (cons (f (car xs)) (map f (cdr xs)))))
(define (filter keep? xs)
  (if (null? xs)
      '()
      (if (keep? (car xs))
          (cons (car xs) (filter keep? (cdr xs)))
          (filter keep? (cdr xs)))))
(define (range a b)
  (if (>= a b) '() (cons a (range (+ a 1) b))))
(define (even? n) (= (modulo n 2) 0))

(show "squares        => " (map (lambda (x) (* x x)) (range 1 11)))
(show "evens          => " (filter even? (range 1 21)))

; a closure counter: each counter keeps its own private n
(define (make-counter)
  (let ((n 0))
    (lambda () (set! n (+ n 1)) n)))
(define c1 (make-counter))
(define c2 (make-counter))
(c1) (c1)
(show "c1 after 3     => " (c1))
(show "c2 after 1     => " (c2))

; a million tail calls run in constant Python stack
(define (count-down n)
  (if (= n 0) 'done (count-down (- n 1))))
(show "(count-down 1000000) => " (count-down 1000000))

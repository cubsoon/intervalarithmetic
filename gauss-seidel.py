#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import getopt

from intervalarithmetic import Interval

def string_from_file(file):
    for line in file:
        strings = line.split()
        for string in strings:
            yield string

def read_interval_left_right(generator):
    left = next(generator)
    right = next(generator)
    return Interval(left, right)

def read_interval(generator):
    value = next(generator)
    return Interval(value)

def read_float(generator):
    value = next(generator)
    return float(value)

def read_data(read_function, verbose=False, input_generator=string_from_file(sys.stdin)):
    if verbose:
        print("Maksymalna ilość iteracji: [liczba naturalna > 1]")
    max_iter = int(next(input_generator))
    if verbose:
        print("Epsilon rozwiązania (względny błąd): [liczba rzeczywista > 0]")
    eps = float(next(input_generator))
    if verbose:
        print("Podaj ilość zmiennych: [liczba naturalna]")
    n = int(next(input_generator))
    if verbose:
        print("Podaj macierz A (wierszami): [n x n liczb]")
    a = [[read_function(input_generator) for _ in range(n)] for _ in range(n)]
    if verbose:
        print("Podaj wektor B: [n liczb]")
    b = [read_function(input_generator) for _ in range(n)]
    return max_iter, eps, n, a, b

def print_data(x, n_iter, verbose=False, output=sys.stdout):
    if verbose:
        print("Ilość iteracji: [liczba naturalna]")
    print(n_iter, file=output)
    if verbose:
        print("Wartości x: [n liczb]")
    for xn in x:
        print(xn, file=output)

def gauss_seidel(max_iter, eps, n, a, b):
    n_iter = max_iter
    sol = [0 for _ in range(n)]
    for current_iter in range(max_iter):
        old_sol = sol[:]
        for i in range(n):
            t = b[i]
            for j in range(n):
                if i != j:
                    t -= sol[j] * a[i][j]
            sol[i] = t / a[i][i]
        if current_iter > 1:
            end_iter = True
            for old_x, x in zip(old_sol, sol):
                if abs(float(x) - float(old_x)) >= abs(eps * float(x)):
                    end_iter = False
                    break
            if end_iter:
                n_iter = current_iter
                break
    return sol, n_iter

def usage():
    pass

def main(argv):
    try:
        shortopts = "hm:o:"
        longopts = ["help", "mode=", "output="]
        opts, args = getopt.getopt(argv, shortopts, longopts)
    except getopt.GetoptError as error:
        print(str(error), file=sys.stderr)
        usage()
        sys.exit(2)
    input_filename = None
    output_filename = None
    mode = "float"
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-m", "--mode"):
            if arg.lower() not in ("float", "interval", "leftright"):
                print(arg + " is not a correct mode", file=sys.stderr)
                usage()
                sys.exit(2)
            mode = arg.lower()
        elif opt in ("-o", "--output"):
            output_filename = arg
        else:
            raise RuntimeError("Unhandled option.")

    if len(args) > 1:
        print("too much arguments", file=sys.stderr)
        usage()
        sys.exit(2)
    elif len(args) == 1:
        input_filename = args[0]

    read_function = None
    if mode == "float":
        read_function = read_float
    elif mode == "interval":
        read_function = read_interval
    elif mode == "leftright":
        read_function = read_interval_left_right
    else:
        raise RuntimeError("Unhandled mode.")

    max_iter, eps, n, a, b = None, None, None, None, None
    if input_filename:
        with open(input_filename, mode='r') as file:
            generator = string_from_file(file)
            max_iter, eps, n, a, b = read_data(read_function, input_generator=generator)
    else:
        max_iter, eps, n, a, b = read_data(read_function, verbose=True)

    x, n_iter = gauss_seidel(max_iter, eps, n, a, b)

    if output_filename:
        with open(output_filename, mode='w') as file:
            print_data(x, n_iter, output=file)
    else:
        print_data(x, n_iter, verbose=True)

if __name__ == "__main__":
    main(sys.argv[1:])
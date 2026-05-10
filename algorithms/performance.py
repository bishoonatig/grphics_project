import time


def compare(func, *args):

    start = time.perf_counter()

    func(*args)

    end = time.perf_counter()

    return end - start

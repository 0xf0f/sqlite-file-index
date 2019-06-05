from functools import wraps
from inspect import isgeneratorfunction


def optional_generator(func):
    """
    A function passed through this decorator will act as either an ordinary
    function, or, if yields occur, as a generator.

    :param func: a function

    :return:
    a wrapper that when called will return a generator
    if yields occur, otherwise, the return value of the function.
    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        call_result = func(*args, **kwargs)

        if isgeneratorfunction(func):
            try:
                first_item = next(call_result)

            except StopIteration as e:
                try:
                    return e.args[0]
                except IndexError:
                    return None

            else:
                @wraps(func)
                def items():
                    yield first_item
                    yield from call_result

                return items()

        else:
            return call_result

    return wrapped


# example code
if __name__ == '__main__':
    @optional_generator
    def print_or_yield_range(count=3, is_generator=False):
        result = []
        for i in range(count):
            if is_generator:
                yield i
            else:
                result.append(i)

        return result

    as_function = print_or_yield_range(is_generator=False)
    as_generator = print_or_yield_range(is_generator=True)

    print('function returned:', as_function)
    print('generator returned:', as_generator)
    for item in as_generator:
        print('generated:', item)

# output
# 0
# 1
# 2
# 3
# 4
# function returned: lol
# generator returned: <generator object print_or_yield_range at 0x000001ED11D51228>
# generated: 0
# generated: 1
# generated: 2
# generated: 3
# generated: 4

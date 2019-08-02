class IteratorStack:
    def __init__(self):
        self.stack = []

    def push(self, iterable):
        self.stack.append(iter(iterable))

    def pop(self):
        return self.stack.pop()

    def __iter__(self):
        return self

    def __next__(self):
        while self.stack:
            try:
                return next(self.stack[-1])

            except StopIteration:
                self.stack.pop()

        raise StopIteration

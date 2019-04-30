import time


class RetryTimeout(Exception):
    pass


class Retry:
    def __init__(
            self,
            tries=float('inf'),
            delay_between_tries=1,
            exception_types=(Exception,),
            exception_checks=()
    ):
        self.tries = tries
        self.delay_between_tries = delay_between_tries
        self.exception_types = exception_types
        self.exception_checks = exception_checks

    def __call__(self, callee, *args, **kwargs):
        tries_remaining = self.tries

        while tries_remaining > 0:
            try:
                return callee(*args, **kwargs)

            except self.exception_types as e:
                for exception_check in self.exception_checks:
                    if exception_check(e):
                        time.sleep(self.delay_between_tries)
                        tries_remaining -= 1
                else:
                    raise e

        raise RetryTimeout

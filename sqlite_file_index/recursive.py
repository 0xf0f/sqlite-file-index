# # This program shows off a python decorator(
# # which implements tail call optimization. It
# # does this by throwing an exception if it is
# # its own grandparent, and catching such
# # exceptions to recall the stack.
#
# import sys
#
# class TailRecurseException:
#   def __init__(self, args, kwargs):
#     self.args = args
#     self.kwargs = kwargs
#
# def tail_call_optimized(g):
#   """
#   This function decorates a function with tail call
#   optimization. It does this by throwing an exception
#   if it is its own grandparent, and catching such
#   exceptions to fake the tail call optimization.
#
#   This function fails if the decorated
#   function recurses in a non-tail context.
#   """
#   def func(*args, **kwargs):
#     f = sys._getframe()
#     if f.f_back and f.f_back.f_back \
#         and f.f_back.f_back.f_code == f.f_code:
#       raise TailRecurseException(args, kwargs)
#     else:
#       while 1:
#         try:
#           return g(*args, **kwargs)
#         except TailRecurseException, e:
#           args = e.args
#           kwargs = e.kwargs
#   func.__doc__ = g.__doc__
#   return func
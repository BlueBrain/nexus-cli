import sys
from blessings import Terminal


def error(message):
    t = Terminal()
    print(t.red(message))
    sys.exit(101)


def success(message):
    t = Terminal()
    print(t.green(message))
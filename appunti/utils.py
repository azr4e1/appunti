from string import punctuation
import sys
from threading import Thread
import time
from functools import wraps

from collections.abc import Callable, MutableMapping
from typing import Optional, Any, ParamSpec, TypeVar, TypeAlias


_WAIT_TIME = 0.08

# from: https://stackoverflow.com/questions/47060133/python-3-type-hinting-for-decorator
Param = ParamSpec('Param')
RetType = TypeVar('RetType')
OriginalFunc: TypeAlias = Callable[Param, RetType]
DecoratedFunc: TypeAlias = Callable[Param, RetType]
Decorator: TypeAlias = Callable[[OriginalFunc], DecoratedFunc]


class PropagatingThread(Thread):
    """
    Thread subclasses to propagate exceptions in the parent context.
    From: https://stackoverflow.com/questions/2829329/catch-a-threads-exception-in-the-caller-thread
    """
    _target: Callable[[Any], Any]
    _args: list[Any]
    _kwargs: MutableMapping[str, Any]

    def run(self) -> None:
        self.exc = None
        try:
            self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, timeout: Optional[float] = None) -> Any:
        super().join(timeout)
        if self.exc:
            raise self.exc

        return self.ret


def spinner(msg: str = "", epilogue: str = "", format: bool = False) -> Decorator:
    # output a decorator that uses these arguments

    # decorator to show a spinner for long functions
    def spinner_with_message(func: OriginalFunc) -> DecoratedFunc:
        spinner_elements = "⣾⣽⣻⢿⡿⣟⣯⣷"

        @wraps(func)
        def threaded(*args: Param.args, **kwargs: Param.kwargs) -> None:
            # spawn a thread for the operation
            thread = PropagatingThread(target=func, args=args, kwargs=kwargs)
            try:
                thread.start()
                # hide the terminal cursor
                sys.stdout.write("\033[?25l")
                sys.stdout.flush()

                # spin as long as thread is executing
                while thread.is_alive():
                    for spin in spinner_elements:
                        spinner_string = f" {spin} {msg}"
                        print(spinner_string, end="\r", flush=True)
                        time.sleep(_WAIT_TIME)

                # get the result
                res = thread.join()

                # format the epilogue
                final_output = epilogue.format(res) if format else epilogue

                # delete the spinner output
                print(" "*len(spinner_string), end="\r", flush=True)

                # print the epilogue
                print(final_output)
            except BaseException as e:
                print(" "*len(spinner_string), end="\r", flush=True)
                print(e)
            finally:
                # show the cursor again
                sys.stdout.write("\033[?25h")
                sys.stdout.flush()

        return threaded
    return spinner_with_message


def ask_for_confirmation(msg: str = "Save note?") -> bool:
    """
    Utility function to ask for confirmation
    """
    response = input(f"{msg} [Y/n]: ")
    commit = True
    if response.lower() in ['n', 'no', 'nope']:
        commit = False

    return commit


def sluggify(title: str) -> str:
    """
    Sluggify the title.

    :param title: title to sluggify.
    :return: sluggified title (duh).
    """
    clean_title = "".join(list(map(lambda x: x
                                   if x not in punctuation or x == "-"
                                   else "", title)))
    slug = clean_title.lower().replace(" ", "-")

    return slug



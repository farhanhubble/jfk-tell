"""Exception monitoring and handling tools"""
from typing import Callable, List
from datetime import datetime
import functools
import time
import traceback
import os

class ExceptionMonitor:
    """Monitor the number of exceptions raised and the number of calls made to a function."""

    def __init__(self, error_rate_threshold: float, min_calls: int):
        """
        :param error_rate_threshold: The error rate threshold in [0,1), above which an exception is raised.
        :param min_calls: The minimum number of calls before the error rate is calculated.
        """
        self.error_rate_threshold = error_rate_threshold
        self.min_calls = min_calls
        self.nb_exceptions = 0
        self.nb_calls = 0
        self.error_rate = 0
        self.exceptions_log = "exceptions.log"
        if os.path.exists(self.exceptions_log):
            os.remove(self.exceptions_log)


    def _save_exception(self):
        with open("exceptions.log", "a") as f:
            f.write(f"{datetime.now()}\n")
            f.write(traceback.format_exc())
            f.write("\n\n")

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.nb_calls += 1
            try:
                return func(*args, **kwargs)
            except Exception:
                self.nb_exceptions += 1
                if self.nb_calls >= self.min_calls:
                    self.error_rate = self.nb_exceptions / self.nb_calls
                    if self.error_rate > self.error_rate_threshold:
                        raise
                self._save_exception()

        return wrapper


def retry_with_backoff(backoffs: List[int], when: Callable[[Exception], bool]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            for backoff in backoffs:
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    if not when(e):
                        raise
                    time.sleep(backoff)
            # Re-raise, if we exhaust all backoffs without success
            else:
                raise

        return wrapper

    return decorator


def skip_silently(when: Callable[[Exception], bool]):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if not when(e):
                    raise
                else:
                    return (
                        "Observations/Remarks:\n\n"
                        "File too large to be processed.\n\n"
                        "```markdown\n\n```"
                    )

        return wrapper

    return decorator

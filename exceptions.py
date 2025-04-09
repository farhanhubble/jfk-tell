"""Exception monitoring and handling tools"""

from collections import deque
from typing import Callable, List
from datetime import datetime
import functools
import time
import traceback
import os


class ExceptionMonitor:
    """Monitor the number of exceptions raised and the number of calls made to a function."""

    def __init__(
        self, error_rate_threshold: float, min_calls: int, window_sz: int = 100
    ):
        """
        :param error_rate_threshold: The error rate threshold in [0,1), above which an exception is raised.
        :param min_calls: The minimum number of calls before the error rate is calculated.
        """
        self.error_rate_threshold = error_rate_threshold
        self.min_calls = min_calls
        self.exceptions_log = "exceptions.log"
        if os.path.exists(self.exceptions_log):
            os.remove(self.exceptions_log)

        if window_sz < min_calls:
            raise ValueError(
                f"Window size {window_sz} must be greater than or equal to min_calls {min_calls}."
            )
        self.window_sz = window_sz
        self.recent_outcomes = deque(maxlen=window_sz)

    def _error_rate_exceeded(self):
        if len(self.recent_outcomes) < self.min_calls:
            return False
        return (
            sum(self.recent_outcomes) / len(self.recent_outcomes)
        ) > self.error_rate_threshold

    def _save_exception(self):
        with open("exceptions.log", "a") as f:
            f.write(f"{datetime.now()}\n")
            f.write(traceback.format_exc())
            f.write("\n\n")

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                self.recent_outcomes.append(False)
                return result
            except Exception:
                self.recent_outcomes.append(True)
                if self._error_rate_exceeded():
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

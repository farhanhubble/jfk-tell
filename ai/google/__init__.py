from config import config
from datetime import datetime
from dotenv import dotenv_values
from httpx import ReadTimeout
import io
from enum import Enum
import functools
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from hashlib import md5
import os
from pathlib import Path
import traceback
import tempfile
import time
from typing import List, Callable


secrets = dotenv_values(config.secrets_file)
GEMINI_API_KEY = secrets["GEMINI_API_KEY"]


class GEMINI_AVAILABLE_MODELS(Enum):
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"


class ExceptionMonitor:
    """ Monitor the number of exceptions raised and the number of calls made to a function. """
    def __init__(self, error_rate_threshold: float, min_calls: int):
        """
        :param error_rate_threshold: The error rate threshold above which an exception is raised.
        :param min_calls: The minimum number of calls before the error rate is calculated.
        """
        self.error_rate_threshold = error_rate_threshold
        self.min_calls = min_calls
        self.nb_exceptions = 0
        self.nb_calls = 0
        self.error_rate = 0

    def _save_exception(self):
        with open("exceptions.log", "a") as f:
            f.write(f"{datetime.now()}\n")
            f.write(traceback.format_exc())
            f.write("\n\n")


    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                self.nb_exceptions += 1
                if self.nb_calls >= self.min_calls:
                    self.error_rate = self.nb_exceptions / self.nb_calls
                    if self.error_rate > self.error_rate_threshold:
                        raise
                self._save_exception()
            finally:
                self.nb_calls += 1
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


def _is_file_size_exceeded(e: Exception):
    return (
        isinstance(e, ClientError)
        and e.code == 400
        and str(e).find(
            "The request's total referenced files bytes are too large to be read"
        )
        >= 0
    )


def _is_server_overloaded(e: Exception):
    return isinstance(e, ServerError) and e.code == 503 and str(e).find("The model is overloaded") >= 0


def _is_file_io_timeout(e: Exception):
    return isinstance(e, ReadTimeout)


def _is_retryable(e: Exception):
    return _is_server_overloaded(e) or _is_file_io_timeout(e)

class GeminiClient:
    def __init__(self, model: GEMINI_AVAILABLE_MODELS, use_local_cache: bool = False):
        self._client = genai.Client(api_key=GEMINI_API_KEY)
        if model not in GEMINI_AVAILABLE_MODELS:
            raise ValueError(
                f"Model {model} not available. Choose from {[k for k in GEMINI_AVAILABLE_MODELS]}"
            )
        self._model = model
        self._use_local_cache = use_local_cache
        if use_local_cache:
            self._cache_dir = config.extraction.cache_dir
            if not self._cache_dir.exists():
                self._cache_dir.mkdir(parents=True)

    @ExceptionMonitor(error_rate_threshold=0.03, min_calls=100)
    @retry_with_backoff([30, 60], when=_is_retryable)
    @skip_silently(when=_is_file_size_exceeded)
    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        attachments: List[Path] | List[io.BytesIO] = [],
        max_tokens: int = None,
    ):

        def _get_cache_key():
            key = md5(prompt.encode())
            if system_prompt:
                key.update(system_prompt.encode())
            for attachment in attachments:
                key.update(attachment.read())
                if isinstance(attachment, io.BytesIO): # https://github.com/farhanhubble/jfk-tell/issues/1
                    attachment.seek(0)
            if max_tokens:
                key.update(str(max_tokens).encode())
            return key.hexdigest()

        if self._use_local_cache:
            cache_key = _get_cache_key()
            cache_file = self._cache_dir / f"{cache_key}"
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    return f.read()

        attached_files = []
        for attachment in attachments:
            try:
                f = self._client.files.upload(
                    file=attachment, 
                    config=dict(mime_type='application/pdf')
                )
                attached_files.append(f)
            except Exception as e:
                raise Exception(f"Failed to upload file {attachment}: {e}") from e
        response = self._client.models.generate_content(
            model=self._model.value,
            contents=attached_files + [prompt],
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                system_instruction=system_prompt or None,
            ),
        )

        if self._use_local_cache:
            temp_file = tempfile.NamedTemporaryFile(delete=False, dir=self._cache_dir)
            try:
                with open(temp_file.name, "w") as f:
                    f.write(response.text or "```markdown\n\n```")
                os.replace(temp_file.name, cache_file)
            finally:
                if os.path.exists(temp_file.name):
                    os.remove(temp_file.name)

        return response.text

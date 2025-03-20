from config import config
from dotenv import dotenv_values
from enum import Enum

from google import genai
from google.genai import types

from hashlib import md5

from pathlib import Path
from typing import List


secrets = dotenv_values(config.secrets_file)
GEMINI_API_KEY = secrets["GEMINI_API_KEY"]


class GEMINI_AVAILABLE_MODELS(Enum):
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"


class GeminiClient:
    def __init__(self, model: GEMINI_AVAILABLE_MODELS, use_local_cache: bool = False):
        self._client = genai.Client(api_key=GEMINI_API_KEY)
        if model not in GEMINI_AVAILABLE_MODELS:
            raise ValueError(
                f"Model {model} not available. Choose from {[k for k in GEMINI_AVAILABLE_MODELS]}"
            )
        self._model = model
        if use_local_cache:
            self._use_local_cache = use_local_cache
            self._cache_dir = Path(".gemini/cache")
            if not self._cache_dir.exists():
                self._cache_dir.mkdir(parents=True)

    def generate(self, prompt:str, system_prompt:str = None, attachments: List[Path]=[], max_tokens:int = None):

        def _get_cache_key():
            key = md5(prompt.encode())
            if system_prompt:
                key.update(system_prompt.encode())
            for attachment in attachments:
                key.update(attachment.read_bytes())
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
                f = self._client.files.upload(file=attachment)
                attached_files.append(f)
            except Exception as e:
                raise Exception(f"Failed to upload file {attachment}: {e}") from e
        response = self._client.models.generate_content(
            model=self._model.value,
            contents= attached_files + [prompt],
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                system_instruction=system_prompt or None,
            )
        )

        if self._use_local_cache:
            with open(cache_file, "w") as f:
                f.write(response.text)

        return response.text

from config import config
from dotenv import dotenv_values
from enum import Enum

from google import genai
from google.genai import types

from pathlib import Path
from typing import List


secrets = dotenv_values(config.secrets_file)
GEMINI_API_KEY = secrets["GEMINI_API_KEY"]


class GEMINI_AVAILABLE_MODELS(Enum):
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"


class GeminiClient:
    def __init__(self, model: GEMINI_AVAILABLE_MODELS):
        self._client = genai.Client(api_key=GEMINI_API_KEY)
        if model not in GEMINI_AVAILABLE_MODELS:
            raise ValueError(
                f"Model {model} not available. Choose from {[k for k in GEMINI_AVAILABLE_MODELS]}"
            )
        self._model = model

    def generate(self, prompt:str, system_prompt:str = None, attachments: List[Path]=[], max_tokens:int = None):
        attached_files = []
        for attachment in attachments:
            try:
                f = self._client.files.upload(attachment)
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

        return response.text

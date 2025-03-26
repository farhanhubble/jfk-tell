from ai.google import GeminiClient
from extract import _model_from_name, _extract_single_file
from pathlib import Path

src = Path("data/archives.gov/2017-2018/104-10001-10004.pdf")
target_dir = Path(".")
client = GeminiClient(_model_from_name("gemini-2.0-flash"))

with open("prompts/extraction/instructions.txt") as f:
    prompt = f.read()

with open("prompts/extraction/system.txt") as f:
    system_prompt = f.read()

_extract_single_file(src, target_dir, client, prompt, system_prompt)
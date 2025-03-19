from ai.google import GeminiClient, GEMINI_AVAILABLE_MODELS
from pathlib import Path


def _model_from_name(name: str) -> GEMINI_AVAILABLE_MODELS:
    try:
        return {k.value: k.name for k in GEMINI_AVAILABLE_MODELS}[name]
    except KeyError:
        raise ValueError(f"Model {name} not available. Choose from {[k for k in GEMINI_AVAILABLE_MODELS]}")
    

def run_extraction(model_name: GEMINI_AVAILABLE_MODELS, prompt_file: Path, system_prompt_file: Path = None, max_tokens: int = None):
    model = _model_from_name(model_name)
    client = GeminiClient(model)
    with open(prompt_file, "r") as f:
        prompt = f.read()
    if system_prompt_file:
        with open(system_prompt_file, "r") as f:
            system_prompt = f.read()
    else:
        system_prompt = None
    return client.generate(prompt, system_prompt, max_tokens)
from ai.google import GeminiClient, GEMINI_AVAILABLE_MODELS
from pathlib import Path
from tqdm import tqdm


def _model_from_name(name: str) -> GEMINI_AVAILABLE_MODELS:
    try:
        return {k.value: k.name for k in GEMINI_AVAILABLE_MODELS}[name]
    except KeyError:
        raise ValueError(f"Model {name} not available. Choose from {[k for k in GEMINI_AVAILABLE_MODELS]}")
    

def extract_all(src_dir: Path, target_dir: Path, model_name: GEMINI_AVAILABLE_MODELS, prompt_file: Path, system_prompt_file: Path = None, max_tokens: int = None ):
    model = _model_from_name(model_name)
    client = GeminiClient(model)
    with open(prompt_file, "r") as f:
        prompt = f.read()
    if system_prompt_file:
        with open(system_prompt_file, "r") as f:
            system_prompt = f.read()
    else:
        system_prompt = None
    
    pdf_files = list(src_dir.glob("*.pdf"))
    if not target_dir.exists():
        target_dir.mkdir(parents=True)
    for pdf_file in tqdm(pdf_files):
        summary_file = target_dir / pdf_file.with_suffix(".txt")
        with open(summary_file, "w") as f:
            f.write(client.generate(prompt, system_prompt, pdf_file, max_tokens))


def extract_single(src: Path, client: GeminiClient, prompt: str, system_prompt: str = None, max_tokens: int = None):
    return client.generate(prompt, system_prompt, [src], max_tokens)
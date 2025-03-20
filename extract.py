from _logging import logger
from ai.google import GeminiClient, GEMINI_AVAILABLE_MODELS
from config import config
from pathlib import Path
from tqdm import tqdm


def _model_from_name(name: str) -> GEMINI_AVAILABLE_MODELS:
    for k in GEMINI_AVAILABLE_MODELS:
        if k.value == name:
            return k
    else:
        raise ValueError(
            f"Model {name} not available. Choose from {[k for k in GEMINI_AVAILABLE_MODELS]}"
        )


def extract_all(
    src_dir: Path,
    target_dir: Path,
    model_name: GEMINI_AVAILABLE_MODELS,
    prompt_file: Path,
    system_prompt_file: Path = None,
    max_tokens: int = None,
):
    logger.info(f"Extracting information from {src_dir} to {target_dir}")
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
    for pdf_file in tqdm(pdf_files, desc="Extracting information from PDFs"):
        extract_file = target_dir / pdf_file.with_suffix(".md").name
        with open(extract_file, "w") as f:
            f.write(_extract_single(pdf_file, client, prompt, system_prompt, max_tokens))


def _parse_llm_response(response: str):
    start = response.find("```markdown")
    if start >= 0:
        start += len("```markdown")
        end = response.find("```", start)
        if end >= 0:
            return response[start:end].strip()
    return response


def _extract_single(
    src: Path,
    client: GeminiClient,
    prompt: str,
    system_prompt: str = None,
    max_tokens: int = None,
):
    raw =  client.generate(prompt, system_prompt, [src], max_tokens)
    return _parse_llm_response(raw)


if __name__ == "__main__":
    SRC = config.extraction.src_dir
    DEST = config.extraction.dest_dir
    MODEL = config.extraction.model_name
    PROMPT_FILE = config.extraction.prompt_file
    SYSTEM_PROMPT_FILE = config.extraction.system_prompt_file
    MAX_TOKENS = config.extraction.max_tokens

    for src_subdir in SRC.iterdir():
        if src_subdir.is_dir():
            extract_all(
                src_subdir,
                DEST / src_subdir.name,
                MODEL,
                PROMPT_FILE,
                SYSTEM_PROMPT_FILE,
                MAX_TOKENS,
            )

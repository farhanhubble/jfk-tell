from _logging import logger
from ai.google import GeminiClient, GEMINI_AVAILABLE_MODELS
from config import config
import io
from multiprocessing import Pool
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from tqdm import tqdm


def _model_from_name(name: str) -> GEMINI_AVAILABLE_MODELS:
    for k in GEMINI_AVAILABLE_MODELS:
        if k.value == name:
            return k
    else:
        raise ValueError(
            f"Model {name} not available. Choose from {[k for k in GEMINI_AVAILABLE_MODELS]}"
        )


def _parse_markdown(response: str):
    start = response.find("```markdown")
    md_content = ""
    if start >= 0:
        start += len("```markdown")
        end = response.find("```", start)
        if end >= 0:
            md_content = response[start:end].strip()
    return md_content


def _load_pdf_pages(pdf_file: Path):
    pdf_data = PdfReader(pdf_file)
    for i, page in enumerate(pdf_data.pages):
        buffer = io.BytesIO()
        writer = PdfWriter()
        writer.add_page(page)
        writer.write(buffer)
        buffer.seek(0)
        yield buffer


class Extractor:
    def __init__(
        self,
        model: GEMINI_AVAILABLE_MODELS,
        prompt_file: Path,
        system_prompt_file: Path = None,
        max_tokens: int = None,
    ):
        self.client = GeminiClient(model)
        with open(prompt_file, "r") as f:
            self.prompt = f.read()
        if system_prompt_file:
            with open(system_prompt_file, "r") as f:
                self.system_prompt = f.read()
        else:
            self.system_prompt = None
        self.max_tokens = max_tokens

    def extract_single_file(
        self,
        src: Path,
        tgt_dir: Path,
    ):
        pages = list(_load_pdf_pages(src))
        extracted_raw = []
        for page in pages:
            extracted_raw.append(self.extract_single_page(page))

        if config.extraction.include_annotation:
            content = "\n\n".join(extracted_raw)
        else:
            content = "\n\n".join(map(_parse_markdown, extracted_raw))

        file_ext = ".txt" if config.extraction.include_annotation else ".md"
        tgt = tgt_dir / src.with_suffix(file_ext).name
        with open(tgt, "w") as f:
            f.write(content or "")

    def extract_single_page(
        self,
        page: io.BytesIO,
    ):
        raw = self.client.generate(
            self.prompt, self.system_prompt, [page], self.max_tokens
        )
        return raw or ""


def _worker(
    pdf_file: str,
    target_dir: str,
    model_name: str,
    prompt_file: str,
    system_prompt_file: str,
    max_tokens: int,
):
    global extractor
    extractor = Extractor(
        _model_from_name(model_name),
        Path(prompt_file),
        Path(system_prompt_file),
        max_tokens,
    )
    extractor.extract_single_file(Path(pdf_file), Path(target_dir))


def __worker_wrapper(args):
    return _worker(*args)


def extract_all(
    src_dir: Path,
    target_dir: Path,
    model_name: str,
    prompt_file: Path,
    system_prompt_file: Path = None,
    max_tokens: int = None,
):
    logger.info(f"Extracting information from {src_dir} to {target_dir}")
    pdf_files = sorted(list(src_dir.glob("*.pdf")))
    if not target_dir.exists():
        target_dir.mkdir(parents=True)

    with Pool(32) as pool:
        list(
            tqdm(
                pool.imap(
                    __worker_wrapper,
                    [
                        (
                            str(pdf_file),
                            str(target_dir),
                            model_name,
                            str(prompt_file),
                            str(system_prompt_file),
                            max_tokens,
                        )
                        for pdf_file in pdf_files
                    ],
                    chunksize=16,
                ),
                total=len(pdf_files),
            )
        )


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

import json
from pydantic import BaseModel, RootModel, Field
from pathlib import Path


class EXTRACTION_CONFIG(BaseModel):
    model_name: str
    prompt_file: Path
    system_prompt_file: Path = None
    max_tokens: int = None
    src_dir: Path
    dest_dir: Path
    include_annotation: bool = Field(
        ..., description="Include LLM-generated remarks in the extracted document"
    )


class Config(BaseModel):
    secrets_file: Path = Field(..., description="Path to the secrets file")
    extraction: EXTRACTION_CONFIG = Field(..., description="Extraction configuration")


with open(".config/default.json", "r") as f:
    config = Config(**json.load(f))


if __name__ == "__main__":
    print(config.model_dump_json(indent=2))

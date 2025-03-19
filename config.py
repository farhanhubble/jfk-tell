import json
from pydantic import BaseModel, RootModel, Field
from pathlib import Path


class Config(BaseModel):
    secrets_file: Path = Field(..., description="Path to the secrets file")


with open(".config/default.json", "r") as f:
    config = Config(**json.load(f))


if __name__  == "__main__":
    print(config.model_dump_json(indent=2))
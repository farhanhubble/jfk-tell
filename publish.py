from huggingface_hub import HfApi
import os
from pathlib import Path
from tqdm import tqdm
import pyarrow as pa
import pyarrow.parquet as pq
from typing import Literal
from typer import Typer

app = Typer()


text_schema = pa.schema([("file_path", pa.string()), ("text", pa.string())])

binary_schema = pa.schema([("file_path", pa.string()), ("content", pa.binary())])


def get_text_file_records(base_dir):
    """
    Yields records from UTF-8 text files in the directory.
    """
    for filepath in base_dir.rglob("*"):
        if not filepath.is_file():
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            yield {"file_path": str(filepath.relative_to(base_dir)), "text": content}
        except Exception as e:
            print(f"Error reading text file {filepath}: {e}")


def get_binary_file_records(base_dir):
    """
    Yields records from binary files in the directory.
    """
    for filepath in base_dir.rglob("*"):
        if not filepath.is_file():
            continue
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            yield {"file_path": str(filepath.relative_to(base_dir)), "content": content}
        except Exception as e:
            print(f"Error reading binary file {filepath}: {e}")


def build_parquet(
    dir_path, parquet_path, schema, content_type:Literal["text", "binary"]
):
    # Check if the file already exists
    if os.path.exists(parquet_path):
        print(f"Deleting existing Parquet file {parquet_path}.")
        os.remove(parquet_path)

    _file_records_fetcher = (
        get_text_file_records if content_type == "text" else get_binary_file_records
    )

    # Create the Parquet file
    with pq.ParquetWriter(parquet_path, schema) as writer:
        for record in tqdm(_file_records_fetcher(dir_path), desc="Processing files"):
            table = pa.Table.from_pylist([record], schema=schema)
            writer.write_table(table)


def publish_hf(parquet_path, repo_name):
    """Push Parquet file to Hugging Face Hub.
    Requires HF login via access token.
    """
    api = HfApi()
    # Create the repo
    api.create_repo(repo_name, exist_ok=True)

    # Upload the Parquet file
    api.upload_file(
        path_or_fileobj=parquet_path,
        path_in_repo=os.path.basename(parquet_path),
        repo_id=repo_name,
        repo_type="dataset",
    )

    print(f"Uploaded {parquet_path} to {repo_name}")


@app.command()
def publish(
    dir_path: Path,
    parquet_path: Path,
    repo_name: str,
    content_type: str,
    dry_run: bool = False,
):
    """
    Publish the contents of a directory to Hugging Face Hub as a Parquet file.
    """
    if content_type not in ["text", "binary"]:
        raise ValueError("content_type must be either 'text' or 'binary'")

    # Build the Parquet file
    build_parquet(
        dir_path,
        parquet_path,
        text_schema if content_type == "text" else binary_schema,
        content_type,
    )

    # Publish to Hugging Face Hub
    print(f"Publishing {parquet_path} to {repo_name}...")
    if dry_run:
        print("Dry run enabled. Not uploading to Hugging Face Hub.")
    else:
        publish_hf(parquet_path, repo_name)


if __name__ == "__main__":
    app()

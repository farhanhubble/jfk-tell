from extract import _worker

src = "data/archives.gov/2017-2018/104-10001-10004.pdf"
target_dir = "."
model_name = "gemini-2.0-flash"

prompt_file = "prompts/extraction/instructions.txt"
system_prompt_file = "prompts/extraction/system.txt"

_worker(src, target_dir, model_name, prompt_file, system_prompt_file, 4096)

# JFK-Tell
Using AI to Analyze the JFK assassination records

## About
This repository contains the code used to download, process and publish the [JFK Archives][1] and [JFK Tell][2] datasets on Hugging Face.

## Setup
If you would like to reproduce this work, You'll need Gemini API access and valid key. Find out how to get a key [here][3]

Then follow the instructions below:

- Install Poetry, e.g. with `PipX` or `HomeBrew`
- Install Python, use `pyenv` if you do not want to affect existing Python interpreters
- Clone this repo
- If using `pyenv` or a similar tool, set your interpreter, e.g. with `pyenv local`
- Run `poetry install` from inside the top-level cloned dir to install all dependencies to a new `Poetry` environment
- Run the appropriate `Poetry` command to activate a shell with the newly created Python environment
- Edit `.dvc/config` and set the `url` to the path where you would like DVC to store data it tracks. 
- Create a file named `.env` inside the `.secrets` directory and add a line like `GEMINI_API_KEY="AI******************************pE"`


<!-- Citations -->
[1]: https://huggingface.co/datasets/farhanhubble/jfk-archives
[2]: https://huggingface.co/datasets/farhanhubble/jfk-tell
[3]: https://ai.google.dev/gemini-api/docs/quickstart?lang=python
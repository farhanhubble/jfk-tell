#! /bin/bash
# Upload extracted data as a single parquet file to HuggingFace Hub
python publish.py data/extracted/ ./jfk-tell.parquet farhanhubble/jfk-tell text

# Upload the PDFs downloaded from the JFK archive, as parquets split by year (HF size restrictions)
python publish.py data/archives.gov/2017-2018/ ./jfk-archive-2017-2018.parquet farhanhubble/jfk-archives binary && rm ./jfk-archive-2017-2018.parquet
python publish.py data/archives.gov/2021/ ./jfk-archive-2021.parquet farhanhubble/jfk-archives binary && rm ./jfk-archive-2021.parquet
python publish.py data/archives.gov/2022/ ./jfk-archive-2022.parquet farhanhubble/jfk-archives binary && rm ./jfk-archive-2022.parquet
python publish.py data/archives.gov/2023/ ./jfk-archive-2023.parquet farhanhubble/jfk-archives binary && rm ./jfk-archive-2023.parquet
python publish.py data/archives.gov/2025/ ./jfk-archive-2025.parquet farhanhubble/jfk-archives binary && rm ./jfk-archive-2025.parquet
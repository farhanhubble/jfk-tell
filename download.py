import os
import pandas as pd
import requests
from _logging import logger
from bs4 import BeautifulSoup
from config import config
from multiprocessing import Pool
from tqdm import tqdm
from urllib.parse import urljoin
from pathlib import Path


def _pdf_list_from_page(page_url):
    logger.info(f"Extracting PDF links from download page: {page_url}")
    response = requests.get(page_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a")
    pdf_links = []

    for link in tqdm(links, desc="Extracting PDF links"):
        href = link.get("href")
        if href and ".pdf" in href.lower():
            pdf_url = urljoin(page_url, href)
            pdf_links.append(pdf_url)

    return list(set(pdf_links))


def _pdf_list_from_metadata(page_url, metadata_url):
    logger.info(f"Extracting PDF links from metadata at: {metadata_url}")
    df = pd.read_excel(metadata_url)
    pdf_links = [urljoin(page_url, href) for href in df["File Name"].tolist()]
    return pdf_links


def download_single_pdf(pdf_url, download_folder):
    try:
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()
        filename = pdf_url.split("/")[-1]
        local_path = os.path.join(download_folder, filename)

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {pdf_url}: {e}")


def download_archive(metadata_url, page_url, download_folder="pdf_downloads"):
    logger.info(f"Downloading PDFs from {page_url} to {download_folder}")
    download_folder = Path(download_folder)
    download_folder.mkdir(parents=True, exist_ok=True)

    pdf_links = (
        _pdf_list_from_metadata(page_url, metadata_url)
        if metadata_url
        else _pdf_list_from_page(page_url)
    )
    tasks = [(pdf_url, str(download_folder)) for pdf_url in pdf_links]
    with Pool(32) as pool:
        list(
            tqdm(
                pool.imap_unordered(lambda args: download_single_pdf(*args), tasks),
                total=len(pdf_links),
                desc="Downloading PDFs",
            )
        )


if __name__ == "__main__":
    sources = config.download.URLS
    download_dir = Path(config.download.download_dir)
    for year, details in sources.items():
        metadata_url = details["metadata_url"]
        page_url = details["data_url"]
        download_archive(metadata_url, page_url, download_dir / year)

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


def _scrape_pdf_links(page_url):
    logger.debug(f"Extracting PDF links from download page: {page_url}")
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


def _next_page_of(page_url):
    """Generate all next page links starting from any given page."""
    while page_url:
        response = requests.get(page_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        yield page_url

        next_page = soup.find("li", class_="next")
        page_url = urljoin(page_url, next_page.a["href"]) if next_page else None


def _collect_pdf_links(start_url):
    pdf_links = []
    progress = tqdm(leave=False)
    for page_url in _next_page_of(start_url):
        progress.set_description(f"Scraping PDF links from {page_url}")
        pdf_links.extend(_scrape_pdf_links(page_url))
    return pdf_links


def _get_pdf_links(download_folder, start_url):
    if (download_folder / "list.txt").exists():
        with open(download_folder / "list.txt", "r") as f:
            pdf_links = f.read().splitlines()
    else:
        pdf_links = _collect_pdf_links(page_url)
        with open(download_folder / "list.txt", "w") as f:
            f.write("\n".join(pdf_links))
    return pdf_links



def _download_single_pdf(pdf_url, download_folder):
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


def _get_single_pdf(args):
    pdf_url, download_folder, download_cache = args
    get_single_pdf(pdf_url, download_folder, download_cache)


def get_single_pdf(pdf_url, download_folder, download_cache):
    filename = pdf_url.split("/")[-1]
    cache_path = os.path.join(download_cache, filename)

    try:
        with open(cache_path, "rb") as f:
            pdf = f.read()
        with open(os.path.join(download_folder, filename), "wb") as f:
            f.write(pdf)
    except Exception as e:
        _download_single_pdf(pdf_url, download_cache)


def download_archive(page_url, download_folder, cache_folder):
    logger.info(f"Downloading PDFs from {page_url} to {download_folder}")
    download_folder = Path(download_folder)
    download_folder.mkdir(parents=True, exist_ok=True)
    pdf_links = _get_pdf_links(download_folder, page_url)

    tasks = [(pdf_url, str(download_folder), str(cache_folder)) for pdf_url in pdf_links]
    with Pool(32) as pool:
        list(
            tqdm(
                pool.imap_unordered(_get_single_pdf, tasks, chunksize=16),
                total=len(pdf_links),
                desc="Downloading PDFs",
            )
        )


if __name__ == "__main__":
    sources = config.download.URLS
    download_dir = Path(config.download.download_dir)
    download_cache = download_dir / ".cache"
    download_cache.mkdir(parents=True, exist_ok=True)
    for year, details in sources.items():
        page_url = details["data_url"]
        download_archive(page_url, download_dir / year, download_cache / year)

import os
import pandas as pd
import requests
from _logging import logger
from bs4 import BeautifulSoup
from config import config
from tqdm import tqdm
from urllib.parse import urljoin


def _pdf_list_from_page(page_url):
    logger.info(f"Extracting PDF links from download page: {page_url}")
    response = requests.get(page_url)
    response.raise_for_status()  # Raise an error if the request failed

    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all links
    links = soup.find_all("a")
    pdf_links = []

    for link in tqdm(links, desc="Extracting PDF links"):
        href = link.get('href')
        if href and '.pdf' in href.lower():
            # Build the absolute URL to the PDF
            pdf_url = urljoin(page_url, href)
            pdf_links.append(pdf_url)

    # Remove duplicates if any
    pdf_links = list(set(pdf_links))
    return pdf_links


def _pdf_list_from_metadata(metadata_url):
    logger.info(f"Extracting PDF links from metadata at: {metadata_url}")
    response = requests.get(metadata_url)
    response.raise_for_status() 

    # Load the excel file
    df = pd.read_excel(metadata_url)
    pdf_links = df["File Name"].tolist()
    return pdf_links

def download_archive(metadata_url, page_url, download_folder="pdf_downloads"):
    print(f"Downloading PDFs from {page_url} to {download_folder}")
    # Create download folder if it doesn't exist
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    # Fetch the page
    response = requests.get(page_url)
    response.raise_for_status()  # Raise an error if the request failed

    # Get all PDF links
    if metadata_url:
        pdf_links = _pdf_list_from_metadata(metadata_url)
    else:
        pdf_links = _pdf_list_from_page(page_url)

    # Download each PDF
    for pdf_url in tqdm(pdf_links, desc="Downloading PDFs"):
        try:
            pdf_response = requests.get(pdf_url, stream=True)
            pdf_response.raise_for_status()
            
            # Extract the filename from the URL
            filename = pdf_url.split('/')[-1]
            local_path = os.path.join(download_folder, filename)

            # Save the PDF locally
            with open(local_path, 'wb') as f:
                for chunk in pdf_response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {pdf_url}: {e}")

if __name__ == "__main__":
    sources = config.download.URLS
    download_dir = config.download.download_dir
    for year in sources:
        metadata_url = sources[year]["metadata_url"]
        page_url = sources[year]["data_url"]
        download_archive(metadata_url, page_url, download_dir / year)

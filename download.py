import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin

def download_archive(page_url, download_folder="pdf_downloads"):
    print(f"Downloading PDFs from {page_url} to {download_folder}")
    # Create download folder if it doesn't exist
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    # Fetch the page
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
    url = "https://www.archives.gov/research/jfk/release-2017-2018"
    download_archive(url, "./data/archives.gov/2017-2018")
    url = "https://www.archives.gov/research/jfk/release-2021"
    download_archive(url, "./data/archives.gov/2021")
    url = "https://www.archives.gov/research/jfk/release-2022"
    download_archive(url, "./data/archives.gov/2022")
    url = "https://www.archives.gov/research/jfk/release-2023"
    download_archive(url, "./data/archives.gov/2023")
    url = "https://www.archives.gov/research/jfk/release-2025"
    download_archive(url, "./data/archives.gov/2025")

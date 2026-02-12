import os
import time
import requests
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "http://www.gacetaoficial.gob.ve"
SEARCH_URL = "http://www.gacetaoficial.gob.ve/gacetas/filtro-avanzado"
DOWNLOAD_DIR = "downloads"
# Rate limiting
DELAY_SECONDS = 0.5

def ensure_download_dir():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"Created directory: {DOWNLOAD_DIR}")

def get_soup(url, params=None):
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching URL {url} with params {params}: {e}")
        return None

def download_file(url, filepath):
    """Download a file from URL to filepath. Returns True on success, False on failure."""
    try:
        print(f"  Downloading {url}...")
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  ✓ Saved to {filepath}")
            return True
        else:
            print(f"  ✗ Failed to download {url} (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"  ✗ Error downloading {url}: {e}")
        return False

def clean_text(text):
    if not text:
        return ""
    return text.strip()

def construct_pdf_url(gaceta_number, date_str, type_str):
    # Date format in table: DD/MM/YYYY
    # URL format: http://www.gacetaoficial.gob.ve/storage/[Year]/[Number]-[Year]-[Month]-[Day]-[Type].pdf
    # Example: 43287-2026-01-02-ORDINARIA.pdf
    
    try:
        # Handle cases with extra spaces
        date_str = date_str.strip()
        day, month, year = date_str.split('/')
        
        # Remove dots from number if present (e.g., 43.287 -> 43287)
        clean_number = gaceta_number.replace('.', '').strip()
        
        # Ensure type is uppercase and clean
        clean_type = type_str.upper().strip()
        
        filename = f"{clean_number}-{year}-{month}-{day}-{clean_type}.pdf"
        url = f"{BASE_URL}/storage/{year}/{filename}"
        
        return url, filename
    except ValueError:
        print(f"Error parsing date or number: '{gaceta_number}', '{date_str}'")
        return None, None
    except Exception as e:
         print(f"Unexpected error constructing URL: {e}")
         return None, None

def scrape_gacetas():
    ensure_download_dir()
    
    print("Fetching gacetas list...")
    soup = get_soup(SEARCH_URL)
    
    if not soup:
        print("Failed to retrieve page content.")
        return
    
    # Find the table by ID
    table = soup.find('table', id='tablaGacetas')
    if not table:
        print("Table with ID 'tablaGacetas' not found!")
        return
    
    tbody = table.find('tbody')
    if not tbody:
        print("No table body found!")
        return
        
    rows = tbody.find_all('tr')
    if not rows:
         print("No rows found in table.")
         return
    
    print(f"Found {len(rows)} gacetas to process.\n")
    
    processed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, row in enumerate(rows, 1):
        cols = row.find_all('td')
        # Expected columns based on debug output:
        # Col 0: Número (e.g., "6.978", "43.305")
        # Col 1: Tipo (ORDINARIA/EXTRAORDINARIA)
        # Col 2: Source (GACETA OFICIAL)
        # Col 3: Fecha (DD/MM/YYYY)
        # Col 4-6: Other metadata
        # Col 7: Ver link
        
        if len(cols) < 4:
            continue
        
        gaceta_number = clean_text(cols[0].get_text())
        gaceta_type = clean_text(cols[1].get_text())
        gaceta_date = clean_text(cols[3].get_text())
        
        # Simple validation
        if not gaceta_number or not gaceta_date:
            continue
            
        pdf_url, filename = construct_pdf_url(gaceta_number, gaceta_date, gaceta_type)
        
        if pdf_url and filename:
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            print(f"[{i}/{len(rows)}] Gaceta {gaceta_number} ({gaceta_date})")
            
            if os.path.exists(filepath):
                print(f"  ✓ Already downloaded")
                skipped_count += 1
            else:
                success = download_file(pdf_url, filepath)
                if success:
                    processed_count += 1
                else:
                    failed_count += 1
        
        # Rate limiting
        time.sleep(DELAY_SECONDS)
    
    print(f"\n{'='*50}")
    print(f"Download Summary:")
    print(f"  Total gacetas: {len(rows)}")
    print(f"  Downloaded: {processed_count}")
    print(f"  Already existed: {skipped_count}")
    print(f"  Failed: {failed_count}")
    print(f"{'='*50}")

if __name__ == "__main__":
    scrape_gacetas()

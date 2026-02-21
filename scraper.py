import os
import time
import requests
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "http://www.gacetaoficial.gob.ve"
SEARCH_URL = "http://www.gacetaoficial.gob.ve/gacetas/filtro-avanzado"
DOWNLOAD_DIR = "downloads"
FAILED_LOG_FILE = "fallo.txt"
# Rate limiting
DELAY_SECONDS = 0.5

def ensure_download_dir():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"Created directory: {DOWNLOAD_DIR}")

def clean_text(text):
    if not text:
        return ""
    return text.strip()

def construct_pdf_url(gaceta_number, date_str, type_str):
    try:
        date_str = date_str.strip()
        day, month, year = date_str.split('/')
        clean_number = gaceta_number.replace('.', '').strip()
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

def load_failed_gacetas():
    failed = set()
    if os.path.exists(FAILED_LOG_FILE):
        with open(FAILED_LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if "Gaceta:" in line:
                    parts = line.split("|")
                    number = parts[0].replace("Gaceta:", "").strip()
                    failed.add(number)
    return failed

def log_failure(url, gaceta_number, reason):
    with open(FAILED_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"Gaceta: {gaceta_number} | URL: {url} | Reason: {reason}\n")

def scrape_gacetas():
    ensure_download_dir()
    failed_gacetas_set = load_failed_gacetas()
    
    abs_download_dir = os.path.abspath(DOWNLOAD_DIR)
    
    session = requests.Session()
    # Add an implicit headers to act like a browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    })
    
    try:
        print(f"Navigating to {SEARCH_URL}...")
        res = session.get(SEARCH_URL, timeout=30)
        res.raise_for_status()
        
        # Get page source to parse with BeautifulSoup
        soup = BeautifulSoup(res.content, 'html.parser')
        
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
            try:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue
                
                gaceta_number = clean_text(cols[0].get_text())
                gaceta_type = clean_text(cols[1].get_text())
                gaceta_date = clean_text(cols[3].get_text())
                
                if not gaceta_number or not gaceta_date:
                    continue
                
                if gaceta_number in failed_gacetas_set:
                    print(f"[{i}/{len(rows)}] Gaceta {gaceta_number} ({gaceta_date})")
                    print(f"  ✗ Skipping (previously failed, registered in {FAILED_LOG_FILE})")
                    skipped_count += 1
                    continue
                    
                pdf_url, filename = construct_pdf_url(gaceta_number, gaceta_date, gaceta_type)
                
                if not pdf_url or not filename:
                    log_failure("Invalid/Parse Error", gaceta_number, "No se pudo construir la URL esperada")
                    failed_count += 1
                    continue
                
                # Retrieve the actual PDF url dynamically to avoid 404/Forbidden issues
                real_pdf_url = None
                details_link_tag = cols[7].find('a') if len(cols) > 7 else None
                if details_link_tag:
                    details_url = details_link_tag.get('href', '')
                    if details_url:
                        try:
                            # Use requests to quickly fetch the detail page
                            det_res = session.get(details_url, timeout=15)
                            det_soup = BeautifulSoup(det_res.content, 'html.parser')
                            for a_tag in det_soup.find_all('a'):
                                href = a_tag.get('href', '')
                                if '.pdf' in href.lower():
                                    real_pdf_url = href
                                    break
                        except Exception as e:
                            print(f"  ✗ Failed to fetch details for {gaceta_number}: {e}")
                
                # Fallback to constructed url if the dynamic fetching fails
                if not real_pdf_url:
                    real_pdf_url = pdf_url
                
                filepath = os.path.join(abs_download_dir, filename)
                print(f"[{i}/{len(rows)}] Gaceta {gaceta_number} ({gaceta_date})")
                
                if os.path.exists(filepath):
                    print(f"  ✓ Already downloaded: {filename}")
                    skipped_count += 1
                else:
                    print(f"  Downloading: {real_pdf_url}...")
                    
                    try:
                        retries = 3
                        success = False
                        for effort in range(retries):
                            auth_res = session.get(real_pdf_url, stream=True, timeout=30)
                            if auth_res.status_code == 200:
                                with open(filepath, 'wb') as f:
                                    for chunk in auth_res.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                success = True
                                break
                            else:
                                print(f"  ⚠ Retry {effort+1}/{retries} - Status {auth_res.status_code}")
                                time.sleep(1)
                                
                        if success:
                            print(f"  ✓ Successfully downloaded: {filename}")
                            processed_count += 1
                        else:
                            print(f"  ✗ Failed to download: {filename}")
                            reason = f"HTTP Error after retries"
                            log_failure(real_pdf_url, gaceta_number, reason)
                            failed_count += 1
                    except Exception as e:
                        print(f"  ✗ Download Exception: {e}")
                        log_failure(real_pdf_url, gaceta_number, f"Download Crash: {str(e)}")
                        failed_count += 1
                
                time.sleep(DELAY_SECONDS)
                
            except Exception as e:
                print(f"  ✗ General Exception processing row {i}: {e}")
                # Try to extract gaceta number if it failed in the middle
                gn = gaceta_number if 'gaceta_number' in locals() else f"Row {i}"
                pu = pdf_url if 'pdf_url' in locals() else "Unknown"
                log_failure(pu, gn, f"General Error: {str(e)}")
                failed_count += 1
        
        print(f"\n{'='*50}")
        print(f"Download Summary:")
        print(f"  Total gacetas: {len(rows)}")
        print(f"  Downloaded: {processed_count}")
        print(f"  Skipped (existing or failed): {skipped_count}")
        print(f"  Failed right now: {failed_count}")
        if failed_count > 0:
            print(f"  Please check {FAILED_LOG_FILE} for details.")
        print(f"{'='*50}")
    
    except Exception as general_error:
        print(f"CRITICAL ERROR: {general_error}")
        log_failure("General Execution", "All", f"Crash: {general_error}")

if __name__ == "__main__":
    scrape_gacetas()


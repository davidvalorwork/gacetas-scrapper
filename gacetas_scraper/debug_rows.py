import requests
from bs4 import BeautifulSoup

SEARCH_URL = "http://www.gacetaoficial.gob.ve/gacetas/filtro-avanzado"

print("Fetching page...")
response = requests.get(SEARCH_URL, params={'pagina': 1})
soup = BeautifulSoup(response.content, 'html.parser')

# Find the correct table
table = soup.find('table', id='tablaGacetas')
if table:
    print("Found table with ID 'tablaGacetas'")
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        print(f"Total rows: {len(rows)}")
        
        # Show first 3 rows structure
        for i, row in enumerate(rows[:3]):
            cols = row.find_all('td')
            print(f"\nRow {i+1} has {len(cols)} columns:")
            for j, col in enumerate(cols):
                text = col.get_text(strip=True)
                print(f"  Col {j}: {text[:50]}")
                # Check for links
                link = col.find('a')
                if link:
                    print(f"    -> Link href: {link.get('href')}")
else:
    print("Table not found!")

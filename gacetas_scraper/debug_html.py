import requests
from bs4 import BeautifulSoup

SEARCH_URL = "http://www.gacetaoficial.gob.ve/gacetas/filtro-avanzado"

print("Fetching page...")
response = requests.get(SEARCH_URL, params={'pagina': 1})
print(f"Status Code: {response.status_code}")
print(f"Content Length: {len(response.content)}")

soup = BeautifulSoup(response.content, 'html.parser')

# Save the HTML to a file for inspection
with open('debug_page.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())
print("Saved HTML to debug_page.html")

# Check for tables
tables = soup.find_all('table')
print(f"\nFound {len(tables)} table(s)")

for i, table in enumerate(tables):
    print(f"\nTable {i+1}:")
    print(f"  Classes: {table.get('class')}")
    print(f"  ID: {table.get('id')}")
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        print(f"  Rows in tbody: {len(rows)}")
        if rows:
            print(f"  First row text: {rows[0].get_text(strip=True)[:100]}")
    else:
        print("  No tbody found")

# Check for DataTable class specifically
datatable = soup.select_one('table.dataTable')
if datatable:
    print("\nFound table with class 'dataTable'")
else:
    print("\nNo table with class 'dataTable' found")
    
# Check if there's a form that needs to be submitted
forms = soup.find_all('form')
print(f"\nFound {len(forms)} form(s)")

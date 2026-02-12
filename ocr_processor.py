import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# Load environment variables
load_dotenv()

# Configuration
DOWNLOADS_DIR = "downloads"
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "gacetas_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "gacetas")

# Tesseract path (optional, if not in PATH)
TESSERACT_PATH = os.getenv("TESSERACT_PATH")
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def connect_to_mongodb():
    """Establish connection to MongoDB"""
    if not MONGO_URI:
        return None
    
    try:
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        
        # Test connection
        client.server_info()
        print(f"✓ Connected to MongoDB: {MONGO_DB_NAME}")
        return collection
    except ImportError:
        print(f"⚠️  pymongo not installed. Install with: pip install pymongo")
        return None
    except Exception as e:
        print(f"⚠️  Could not connect to MongoDB: {e}")
        return None

def parse_filename(filename):
    """
    Parse gaceta filename to extract metadata
    Format: [Number]-[Year]-[Month]-[Day]-[Type].pdf
    Example: 43287-2026-01-02-ORDINARIA.pdf
    """
    try:
        name = filename.replace('.pdf', '')
        parts = name.split('-')
        
        if len(parts) >= 5:
            return {
                'numero': parts[0],
                'fecha': f"{parts[3]}/{parts[2]}/{parts[1]}",  # DD/MM/YYYY
                'tipo': parts[4],
                'year': parts[1],
                'month': parts[2],
                'day': parts[3]
            }
        return None
    except Exception as e:
        print(f"  ✗ Error parsing filename {filename}: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF using Tesseract OCR
    """
    try:
        print(f"  Converting PDF to images...")
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        
        extracted_text = []
        total_pages = len(images)
        
        print(f"  Processing {total_pages} pages with OCR...")
        for i, image in enumerate(images, 1):
            print(f"    Page {i}/{total_pages}...", end='\r')
            # Extract text from image using Tesseract
            text = pytesseract.image_to_string(image, lang='spa')
            extracted_text.append({
                'page_number': i,
                'text': text.strip()
            })
        
        print(f"  ✓ Extracted text from {total_pages} pages")
        return extracted_text
    except Exception as e:
        print(f"  ✗ Error extracting text: {e}")
        return None

def process_gaceta(pdf_path, collection):
    """
    Process a single gaceta PDF: extract text and save to MongoDB
    """
    filename = os.path.basename(pdf_path)
    
    # Check if already processed
    existing = collection.find_one({'filename': filename})
    if existing:
        print(f"  ✓ Already processed")
        return True
    
    # Parse metadata from filename
    metadata = parse_filename(filename)
    if not metadata:
        print(f"  ✗ Could not parse filename")
        return False
    
    # Extract text using OCR
    pages_text = extract_text_from_pdf(pdf_path)
    if not pages_text:
        return False
    
    # Combine all page texts
    full_text = "\n\n".join([page['text'] for page in pages_text])
    
    # Prepare document for MongoDB
    document = {
        'filename': filename,
        'numero_gaceta': metadata['numero'],
        'fecha': metadata['fecha'],
        'tipo': metadata['tipo'],
        'year': int(metadata['year']),
        'month': int(metadata['month']),
        'day': int(metadata['day']),
        'total_pages': len(pages_text),
        'pages': pages_text,
        'full_text': full_text,
        'processed_at': datetime.utcnow(),
        'file_path': str(pdf_path)
    }
    
    # Insert into MongoDB
    try:
        result = collection.insert_one(document)
        print(f"  ✓ Saved to MongoDB (ID: {result.inserted_id})")
        return True
    except Exception as e:
        print(f"  ✗ Error saving to MongoDB: {e}")
        return False

def process_all_gacetas():
    """
    Process all PDF files in the downloads directory
    """
    # Connect to MongoDB
    collection = connect_to_mongodb()
    
    if not collection:
        print("\n" + "="*50)
        print("⚠️  MongoDB no está configurado o no disponible")
        print("="*50)
        print("\nPara usar MongoDB, configura las credenciales en el archivo .env:")
        print("  1. Copia .env.example a .env")
        print("  2. Edita .env y configura MONGO_URI")
        print("\nEjemplos de MONGO_URI:")
        print("  - Local: mongodb://localhost:27017/")
        print("  - Atlas: mongodb+srv://user:pass@cluster.mongodb.net/")
        print("  - Docker: mongodb://localhost:27017/")
        print("\n" + "="*50)
        print("🧪 Ejecutando modo de prueba (test mode)...")
        print("="*50)
        return test_mode()
    
    # Get all PDF files
    downloads_path = Path(DOWNLOADS_DIR)
    if not downloads_path.exists():
        print(f"✗ Downloads directory not found: {DOWNLOADS_DIR}")
        return
    
    pdf_files = list(downloads_path.glob("*.pdf"))
    total_files = len(pdf_files)
    
    if total_files == 0:
        print(f"✗ No PDF files found in {DOWNLOADS_DIR}")
        return
    
    # Sort PDFs by year (descending: 2026, 2025, 2024...)
    def get_year_from_filename(pdf_path):
        """Extract year from filename for sorting"""
        metadata = parse_filename(pdf_path.name)
        if metadata:
            try:
                return int(metadata['year'])
            except (ValueError, KeyError):
                return 0
        return 0
    
    pdf_files.sort(key=get_year_from_filename, reverse=True)
    
    print(f"\nFound {total_files} PDF files to process")
    print(f"Processing order: Newest first (2026 → 2025 → 2024...)\n")
    
    processed = 0
    failed = 0
    skipped = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{total_files}] Processing: {pdf_path.name}")
        
        # Check if already in database
        existing = collection.find_one({'filename': pdf_path.name})
        if existing:
            print(f"  ✓ Already in database")
            skipped += 1
            continue
        
        success = process_gaceta(pdf_path, collection)
        if success:
            processed += 1
        else:
            failed += 1
        
        print()  # Empty line for readability
    
    # Summary
    print(f"\n{'='*50}")
    print(f"OCR Processing Summary:")
    print(f"  Total files: {total_files}")
    print(f"  Processed: {processed}")
    print(f"  Already in DB: {skipped}")
    print(f"  Failed: {failed}")
    print(f"{'='*50}")

def test_mode():
    """
    Test mode: Extract text from one PDF and print it
    """
    downloads_path = Path(DOWNLOADS_DIR)
    if not downloads_path.exists():
        print(f"\n✗ Downloads directory not found: {DOWNLOADS_DIR}")
        print("  Ejecuta primero: python scraper.py")
        return
    
    pdf_files = list(downloads_path.glob("*.pdf"))
    if not pdf_files:
        print(f"\n✗ No PDF files found in {DOWNLOADS_DIR}")
        print("  Ejecuta primero: python scraper.py")
        return
    
    # Sort PDFs by year (descending: 2026, 2025, 2024...)
    def get_year_from_filename(pdf_path):
        """Extract year from filename for sorting"""
        metadata = parse_filename(pdf_path.name)
        if metadata:
            try:
                return int(metadata['year'])
            except (ValueError, KeyError):
                return 0
        return 0
    
    pdf_files.sort(key=get_year_from_filename, reverse=True)
    
    # Take the first PDF (newest)
    test_pdf = pdf_files[0]
    print(f"\n📄 Archivo de prueba: {test_pdf.name}")
    print("="*50)
    
    # Parse metadata
    metadata = parse_filename(test_pdf.name)
    if metadata:
        print(f"\n📋 Metadata:")
        print(f"  Número: {metadata['numero']}")
        print(f"  Fecha: {metadata['fecha']}")
        print(f"  Tipo: {metadata['tipo']}")
    
    print(f"\n🔄 Extrayendo texto con OCR...")
    print("="*50)
    
    # Extract text
    pages_text = extract_text_from_pdf(test_pdf)
    
    if not pages_text:
        print("\n✗ No se pudo extraer texto del PDF")
        return
    
    # Print results
    print(f"\n✅ Texto extraído exitosamente!")
    print(f"Total de páginas: {len(pages_text)}\n")
    print("="*50)
    print("📝 CONTENIDO DE LA PRIMERA PÁGINA:")
    print("="*50)
    print(pages_text[0]['text'][:1000])  # First 1000 characters
    if len(pages_text[0]['text']) > 1000:
        print("\n... (texto truncado, mostrando primeros 1000 caracteres)")
    
    print("\n" + "="*50)
    print("✅ Prueba completada exitosamente!")
    print("="*50)
    print("\nPara procesar TODAS las gacetas y guardarlas en MongoDB:")
    print("  1. Configura MongoDB en el archivo .env")
    print("  2. Ejecuta nuevamente: python ocr_processor.py")
    print("="*50)

if __name__ == "__main__":
    print("Gaceta OCR Processor")
    print("="*50)
    
    # Check if Tesseract is available
    try:
        pytesseract.get_tesseract_version()
        print("✓ Tesseract OCR is available")
    except Exception as e:
        print("✗ Tesseract OCR not found!")
        print("  Please install Tesseract OCR:")
        print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  Linux: sudo apt-get install tesseract-ocr tesseract-ocr-spa")
        print("  Mac: brew install tesseract tesseract-lang")
        sys.exit(1)
    
    print()
    process_all_gacetas()


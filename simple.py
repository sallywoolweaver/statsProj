import pdfplumber
import pytesseract
from PIL import Image

pdf_file_path = "stats2.pdf"

# Extract data from the PDF using OCR
def extract_text_with_ocr(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"\nProcessing Page: {page_num + 1}")

            # Convert page to image
            page_image = page.to_image(resolution=300)
            pil_image = page_image.original

            # Use OCR to extract text
            ocr_text = pytesseract.image_to_string(pil_image)
            print(ocr_text)

# Run the function
extract_text_with_ocr(pdf_file_path)

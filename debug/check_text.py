import numpy as np
import cv2, pytesseract, os, re, nltk
from PIL import Image
from pdf2image import convert_from_path
from dotenv import load_dotenv
from spellchecker import SpellChecker
from nltk.tokenize import word_tokenize

load_dotenv()
pytesseract.pytesseract.tesseract_cmd = "C:\\Users\\OFFICE\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"

def preprocess_image(pil_image):
    # convert pil image to opencv
    image = np.array(pil_image.convert("L"))
    _, processed = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return Image.fromarray(processed)

def preprocess_text(text: str):
    """
    Clean up the text to remove:
        1. urls
        2. html tags
        3. punctuation
        4. extra spaces
    """

    spell = SpellChecker()

    text = text.lower() # convert to lewercase
    text = re.sub(r"http\s +", "" , text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    tokenized = word_tokenize(text)
    corrected = [spell.correction(word) if word not in spell and word not in nltk.corpus.words.words() 
                 else word for word in tokenized]
    
    return " ".join(corrected)

def extract_text(pdf_path, poppler_path=None):
    """
    Convert the pdf to image (since pdf containes scanned documents that are basically images)
    Then run tesseract ocr to extract text
    Returns the extracted text as a single string
    """
    try:
        images = convert_from_path(pdf_path, poppler_path="C:\\Users\\OFFICE\\Documents\\poppler-24.08.0\\Library\\bin", dpi=300)
        text=""
        for image in images:
            clean_image = preprocess_image(image)
            text+=pytesseract.image_to_string(clean_image) + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""
    
file_name = "Approval_ALEJANDRA-SALINAS_02-14-1982_AZELAIC"

pdf_path = os.path.join("D:\\faxes\\dates\\05-08-2025\\approvals", 
                        f"{file_name}.pdf")

print(f"Raw text:\n{extract_text(pdf_path=pdf_path)}")
print(f"\nProcessed text:\n{preprocess_text(extract_text(pdf_path=pdf_path))}")
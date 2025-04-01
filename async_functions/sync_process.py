import os, re, cv2, numpy as np
from PIL import Image
from nltk.tokenize import word_tokenize
from spellchecker import SpellChecker
import nltk
import pytesseract
from pdf2image import convert_from_path

from nlp.nlp_analysis import determine_letter_type, extract_patient, rename_and_move_pdf

nltk.download('punkt_tab')
nltk.download('words')

def preprocess_image(pil_image):
    image = np.array(pil_image.convert("L"))
    _, processed = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(processed)

def extract_text(pdf_path, poppler_path, tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    try:
        images = convert_from_path(pdf_path, poppler_path=poppler_path)
        text = ""
        for image in images:
            clean_image = preprocess_image(image)
            text += pytesseract.image_to_string(clean_image) + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def preprocess_text(text: str):
    spell = SpellChecker()

    text = text.lower()
    text = re.sub(r"http\s+", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    tokenized = word_tokenize(text)
    corrected = [spell.correction(word) if word not in spell and word not in nltk.corpus.words.words() else word for word in tokenized]
    corrected = [word if word is not None else tokenized[i] for i, word in enumerate(corrected)]
    return " ".join(corrected)

def process_downloaded_pdfs(results, poppler_path, base_path, tesseract_path):
    done = 0
    failed = 0
    pa_approvals = 0
    pa_denials = 0
    pa_requests = 0

    for pdf_path, item in results:
        if pdf_path and os.path.exists(pdf_path):
            raw_text = extract_text(pdf_path, poppler_path = poppler_path, tesseract_path=tesseract_path)
            processed_text = preprocess_text(raw_text)

            letter_type = determine_letter_type(processed_text)
            match letter_type:
                case "approval":
                    pa_approvals += 1
                case "denial":
                    pa_denials += 1
                case "request":
                    pa_requests += 1

            print(f"\nLetter type of {item.get('ID')}: {letter_type}")
            patient_info = extract_patient(raw_text)
            print(f"Patient info: {patient_info}")

            rename_and_move_pdf(
                pdf_path=pdf_path,
                letter_type=letter_type,
                patient_info=patient_info,
                base_path=base_path,
                id=item.get('ID')
            )
            done += 1
        else:
            failed += 1

    print(f"\nCompleted: {done}, Failed: {failed}")
    print(f"Approvals: {pa_approvals}, Denials: {pa_denials}, Requests: {pa_requests}")

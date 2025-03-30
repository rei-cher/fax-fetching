import json, requests, os, pytesseract, time, re, string, nltk, cv2
import numpy as np
from PIL import Image
from nltk.tokenize import word_tokenize
from spellchecker import SpellChecker
from pdf2image import convert_from_path
from dotenv import load_dotenv
from nlp.nlp_analysis import determine_letter_type, extract_patient, rename_and_move_pdf

load_dotenv()
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")
nltk.download('punkt_tab')
nltk.download('words')


def preprocess_image(pil_image):
    # convert pil image to opencv
    image = np.array(pil_image.convert("L"))
    _, processed = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return Image.fromarray(processed)

def extract_text(pdf_path, poppler_path):
    """
    Convert the pdf to image (since pdf containes scanned documents that are basically images)
    Then run tesseract ocr to extract text
    Returns the extracted text as a single string
    """
    try:
        images = convert_from_path(pdf_path, poppler_path=poppler_path)
        text=""
        for image in images:
            clean_image = preprocess_image(image)
            text+=pytesseract.image_to_string(clean_image) + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""
    
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
    corrected = [word if word is not None else tokenized[i] for i, word in enumerate(corrected)]
    return " ".join(corrected)


def fetch_and_analyze(url, token, location, path, date, poppler_path):
    done = 0
    failed = 0
    pa_approvals = 0
    pa_denials = 0
    pa_requests = 0

    # read the json dump that contains the list of faxes
    with open (f"{path}\\dump-{date}.json", 'r') as file:
        data = json.load(file)
        total = len(data["data"])

        for i, item in enumerate(data["data"]):

            """
            There is an issue with rapid pdf download requests
            Catches susspecious activity (stops after 23rd request)
            To avoid - throttling requests (found every 20 is a good spot)
            For future, sleep time may be adjust for better performance (not tested the best time)
            """

            print(f"Doing pdf #: {item.get('ID')}\n{i+1}\\{total}")
            pdf_id = item.get("ID")
            # pdf_id = "33aa15f6-76dd-43ad-9beb-ce61643103c4" __»*. Denying your request for Pimecrolimus 1% services effective 3/26/2025.
            # pdf_id = "98ee7b52-0e4a-4c50-af07-1551eee595f6"
            pdf_url = f"{url}/{pdf_id}"

            try:
                response = requests.get(
                    pdf_url, 
                    headers={
                        "content-type": "application/pdf",
                        'Authorization' : f'Bearer {token}',
                        'Location-id': location,
                    }
                )
            except requests.exceptions.ConnectionError:
                print(f"Download of {item.get('ID')} failed due to exceed of requests\nWaiting 20 seconds, then retrying.")
                time.sleep(20)
                response = requests.get(
                    pdf_url, 
                    headers={
                        "content-type": "application/pdf",
                        'Authorization' : f'Bearer {token}',
                        'Location-id': location,
                    }
                )

            if (response.status_code != 200):
                print(f"Error with {item.get("ID")}, status code: {response.status_code}")
                failed+=1
                continue

            # Save the pdf temporarily
            pdf_dump_dir = os.path.join(path, "pdf_dump")
            if not os.path.exists(pdf_dump_dir):
                os.mkdir(pdf_dump_dir)

            temp_pdf_path = os.path.join(pdf_dump_dir, f"pdf-{pdf_id}.pdf")
            with open(temp_pdf_path, 'wb') as pdf_file:
                pdf_file.write(response.content)

            if os.path.exists(temp_pdf_path):
                # Extract text from pdf (in memory)
                raw_text = extract_text(temp_pdf_path, poppler_path=poppler_path)
                processed_text = preprocess_text(raw_text)
                # print(f"\nText for pdf #: {item.get('ID')}\n{processed_text}\n")

                # Analyze text: type and patient info
                letter_type = determine_letter_type(processed_text)
                match (letter_type):
                    case "approval":
                        pa_approvals +=1
                    case "denial":
                        pa_denials +=1
                    case "request":
                        pa_requests +=1

                print(f"\nLetter type of #: {item.get('ID')} - {letter_type}\n")

                patient_info = extract_patient(raw_text)
                print(f"\nPatient name: {patient_info}\n")

                # Rename and more pdf to corresponding folder
                rename_and_move_pdf(
                    pdf_path=temp_pdf_path,
                    letter_type=letter_type,
                    patient_info=patient_info,
                    base_path=path,
                    id=item.get('ID')
                )
            else:
                print(f"{temp_pdf_path} does not exist")
            done += 1

        # os.remove(pdf_dump_dir)
        print(f"Completed {done}/{total}\nFailed {failed}/{total}")
        print(f"Approvals: {pa_approvals}\nDenials: {pa_denials}\nRequests: {pa_requests}")

def text_extracting(url, token, location, path, date, poppler_path):
    """
    Wrapper function that calls fetch_and_analyze
    (Preserved name 'text_extracting' for backward compatibility with main.py)
    """
    fetch_and_analyze(
        url=url,
        token=token,
        location=location,
        path=path,
        date=date,
        poppler_path=poppler_path
    )

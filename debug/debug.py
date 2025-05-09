import json, requests, os, pytesseract, time
from datetime import datetime, timedelta
from pdf2image import convert_from_path
from dotenv import load_dotenv

load_dotenv()
dateL = (datetime.now() - timedelta(days=1)).strftime("%m-%d-%Y")
path = "C:\\Users\\OFFICE\\Documents\\dump"
pytesseract.pytesseract.tesseract_cmd = r'C:\\Users\\OFFICE\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'

def save_text(text, id):
    with open(f"{path}\\text_dump\\txt-{id}.txt", "w+") as textfile:
        textfile.write(text)

def extract_text(path):
    try:
        images = convert_from_path(path, poppler_path="C:\\Users\\OFFICE\\Documents\\poppler-24.08.0\\Library\\bin")

        text=""
        for image in images:
            text+=pytesseract.image_to_string(image) + "\n"

        return text
    except Exception as e:
        print(f"Failed to extract text from image due: {e}")

def fetch_and_save(date, id="15bab3a8-16d5-4c00-a74e-341d54c1f187"):
    response = requests.get(f"https://api.weaveconnect.com/portal/v1/fax/{id}", headers={
        "content-type": "application/pdf",
        'Authorization' : f'Bearer {os.getenv("AUTHORIZATION")}',
        'Location-id': os.getenv("LOCATION_ID"),
    })
    if (response.status_code == 500):
        print(f"Error with {id}")
    else:
        temp = f"{path}\\pdf_dump\\pdf-{id}.pdf"
        with open(temp, 'wb') as pdf:
            pdf.write(response.content)
        save_text(extract_text(temp), id)
        
        os.remove(temp)

def text_extracting(date):
    if (os.path.isdir(f"{path}\\text_dump")):
        fetch_and_save(date=date)
    else:
        os.mkdir(os.path.join(path, "text_dump"))
        fetch_and_save(date=date)

# text_extracting(date=dateL)

print(datetime.today())
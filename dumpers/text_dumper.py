import json, requests, os, pytesseract, time
from pdf2image import convert_from_path
from dotenv import load_dotenv

# TODO: Move path to env
load_dotenv()
path = "C:\\Users\\OFFICE\\Documents\\dump"
pytesseract.pytesseract.tesseract_cmd = r'C:\\Users\\OFFICE\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'

def save_text(text, id):
    with open(f"{path}\\text_dump\\txt-{id}.txt", "w+") as textfile:
        textfile.write(text)

def extract_text(path, id):
    try:
        images = convert_from_path(path, poppler_path="C:\\Users\\OFFICE\\Documents\\poppler-24.08.0\\Library\\bin")

        text=""
        for image in images:
            text+=pytesseract.image_to_string(image) + "\n"

        return text
    except Exception as e:
        print(f"Error trying extracting text for {id}")
        pass

def fetch_and_save(date):
    done = 0
    failed = 0
    with open (f"{path}\\dump-{date}.json", 'r') as file:
        data = json.load(file)
        total = len(data["data"])
        for i, item in enumerate(data["data"]):
            if (i % 20 == 0):
                time.sleep(10)
            print(f"Doing request for {item.get("ID")}")
            response = requests.get(f"https://api.weaveconnect.com/portal/v1/fax/{item.get("ID")}", headers={
                "content-type": "application/pdf",
                'Authorization' : f'Bearer {os.getenv("AUTHORIZATION")}',
                'Location-id': os.getenv("LOCATION_ID"),
            })
            if (response.status_code != 200):
                print(f"Error with {item.get("ID")}, status code: {response.status_code}")
                failed+=1
            else:
                temp = f"{path}\\pdf_dump\\pdf-{item.get("ID")}.pdf"
                with open(temp, 'wb') as pdf:
                    pdf.write(response.content)
                save_text(extract_text(temp, id=item.get("ID")), item.get("ID"))
                done+=1
            
                os.remove(temp)
        print(f"Completed {done}/{total}\nFailed {failed}/{total}")

def text_extracting(date):
    if (os.path.isdir(f"{path}\\text_dump")):
        fetch_and_save(date=date)
    else:
        os.mkdir(os.path.join(path, "text_dump"))
        fetch_and_save(date=date)

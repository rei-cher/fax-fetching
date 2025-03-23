import json, requests, os, pytesseract, time
from pdf2image import convert_from_path
from dotenv import load_dotenv
from nlp.nlp_analysis import determine_letter_type, extract_patient, rename_and_move_pdf

load_dotenv()
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")

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
            text+=pytesseract.image_to_string(image) + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}")
        return ""

def fetch_and_analyze(url, token, location, path, date, poppler_path):
    done = 0
    failed = 0

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
            if (i % 20 == 0) and (i != 0):
                time.sleep(10)

            pdf_id = item.get("ID")
            pdf_url = f"{url}/{pdf_id}"

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

            # Extract text from pdf (in memory)
            text = extract_text(temp_pdf_path, poppler_path=poppler_path)

            # Analyze text: type and patient info
            letter_type = determine_letter_type(text)
            patient_info = extract_patient(text)

            # Rename and more pdf to corresponding folder
            rename_and_move_pdf(
                pdf_path=temp_pdf_path,
                letter_type=letter_type,
                patient_info=patient_info,
                base_path=path
            )

            done += 1

        os.remove(pdf_dump_dir)
        print(f"Completed {done}/{total}\nFailed {failed}/{total}")

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

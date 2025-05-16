import cv2, pytesseract, re, os, json, time, requests, shutil
from pdf2image import convert_from_path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from symspellpy.symspellpy import SymSpell, Verbosity

load_dotenv()

url = os.getenv("URL_REQUEST")
location = os.getenv("LOCATION_ID")

pytesseract.pytesseract.tesseract_cmd = "C:\\Users\\OFFICE\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"
        

insurance_types = [
    "Healthfirst",
    "Wellpoint",
    "Fidelis Care",
    "Prime Therapeutics",    # Private horizon
    "Clover Health",
    "UnitedHealthcare",    # UnitedHealthCare
    "Express Scripts",
    "WellCare",
    "Aetna",
    "Horizon",
    "CVS Caremark"
]

approval_patterns = [
    r"has been approved",
    r"Type of coverage approved: Prior Authorization",
    r"Type of coverage approved: Non-Formulary",
    r"pproved for",
    r"This drug has been approved",
    r"This request has been reviewed and approved for the following time period",
    r"Approved for",
    r"approved the requast as follows",
    r"the request is approved for the following time period",
    r"writing to let you know that we have approved",
    r"APPROVAL NOTICE",
    r"Prior Authorization Status: Approved",
    r"no prior authorization required",
    r"We've approved your request for coverage",
]

# TODO: adjust denial letter patters 
denial_patterns = [
    r"Reason for Denial:",
    r"__X__ Denying your request for",
    r"__X__Denying your request for",
    r"__X%__Denying your request for",
    r"__X%___Denying your request for",
    r"RE: Denial of request for coverage",
    r"denied the request for the following reason",
    r"We are unable to approve your request for this drug",
    r"denied the prior authorization",
    r"After reviewing the information sent with your request, it was determined that this request does not meet the criteria for medical necessity",

]

request_patterns = [
    r'RE: Prior Authorization Request',
    r'is waiting for their medication',
    r'A Prior Authorization has been started for',
    r'the PA started for your patient',
    r'has been rejected and requires prior authorization',
    r'ALTERNATIVE REQUESTED :NOT COVERED',
    r'Prior Authorization has already been created',
    r'A Prior Authorization has been started  for',
    r'RESPONSE REQUESTED:  Please send a new prescription',
    r'PRIOR AUTHORIZATION REQUEST',
    r'Your request for prior authorization has been denied. Complete and fax this appeal to the plan today so your patient can receive their medication'
]

received_request_patterns = [
    r'Request Status: Received'
]

trash_pattern = [
    r"Duplicate request. An approved prior authorization is already in the system"
]

clinical_pattern = [
    r'clinical review'
]

def determine_letter_type(text):
    for pattern in approval_patterns:
        if re.search(pattern, text):
            return "Approval"
    for pattern in denial_patterns:
        if re.search(pattern, text):
            return "Denial"
    for pattern in request_patterns:
        if re.search(pattern, text):
            return "PA-Request"
    for pattern in received_request_patterns:
        if re.search(pattern, text):
            return "Received-Request"
    for pattern in trash_pattern:
        if re.search(pattern, text):
            return "Trash"
    for pattern in clinical_pattern:
        if re.search(pattern, text):
            return "Clinical"

def determine_insurance(text):
    """
    From the extracted ocr text, matching the words with the list of pre-exist insurances.
    If there is a match, returns the name of the insurance.
    """
    return next((insurance for insurance in insurance_types if insurance.lower() in text.lower()), None)


# TODO: make a function to extract patinet's info from the denial letters 
def find_approval_entities(text, insurance):
    """
    Based on the extracted ocr text and insurnace type from determine_insurance, get the patient info.
    For each insurance there is its own regex for patient info.
    """

    patient_name = None
    patient_dob = None
    patient_drug = None

    match insurance:
        case "Healthfirst":
            patient_name_match = re.search(r'Member Name:\s*(.*?)\s+Member\b', text) or re.search(r'Dear ([A-Z ]+):', text)
            patient_drug_match = re.search(r'drug\(s\):\s*\n*\s*([A-Z][A-Z0-9]+)', text) or re.search(r'approved your ([A-Za-z0-9 %]+)\.', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "Wellpoint":
            patient_info_match = re.search(r'Member:\s*\d+,\s*([A-Za-z\s]+),\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'follows:\s*\n*\s*([A-Z][A-Z0-9]+)', text)
            if patient_info_match:
                patient_name = patient_info_match.group(1).strip().replace(" ", "-")
                patient_dob = patient_info_match.group(2).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1)

        case "Fidelis Care":
            patient_name_match = re.search(r'Member:\s*([A-Za-z\s\-]+)\s+ID', text) or re.search(r'Member Name:\s*([A-Za-z\s\-]+)\s+Member', text)
            patient_dob_match = re.search(r'DOB:\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'Question:\s*\n*\s*([A-Z][A-Z0-9]+)', text) or re.search(r'Service:\s*\n*\s*([A-Z][A-Z0-9]+)', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1)
        
        case "Horizon":
            pattern = re.search(r'(?:has|hag) (?:requested|requosted)\s+([A-Za-z\s]+?)\s+for\s+([A-Z\s]+?),\s*(?:ID|1D|\[D)\s*#\s*\d+,\s*DOB\s*(\d{1,2}/\d{1,2}/\d{4})', text, re.DOTALL)
            if pattern:
                patient_name = pattern.group(2).replace('\n', ' ').strip().replace(" ", "-")
                patient_dob = pattern.group(3).strip().replace("/", "-")
                patient_drug = pattern.group(1).strip().split(" ")[0]
        
        case "Prime Therapeutics":
            patterns = [
                r'regarding:\s+([A-Z ]+?)\s+Drug:\s+(.+?)\s+Date of Birth:.*?(\b\d{1,2}/\d{1,2}/\d{4}\b)',
                r'Name:\s+(.+?)\s+First Name:\s+([A-Za-z\-]+)\s+Strength:.*?Last Name:\s+([A-Za-z\-]+).*?Date of Birth:\s+(\d{1,2}/\d{1,2}/\d{4})',
                r'Re:\s*([A-Z\s\-]+?)\s+Member\s*DOB:\s*(\d{1,2}/\d{1,2}/\d{4}).*?Why we are writing:\s*([A-Z0-9 .%/-]+?)\s+has been'
            ]

            for pattern in patterns:
                result = re.search(pattern, text)
                if result:
                    if pattern.startswith('regarding:'):
                        patient_name = result.group(1).strip().replace(" ", "-")
                        patient_drug = result.group(2).strip().split(" ")[0]
                        patient_dob = result.group(3).strip().replace("/", "-")

                    elif pattern.startswith('Re:'):
                        patient_name = result.group(1).strip().replace(" ", "-")
                        patient_dob = result.group(2).strip().replace("/", "-")
                        patient_drug = result.group(3).strip().split(" ")[0]

                    elif pattern.startswith('Name'):  # Last pattern (drug name first, then first/last name, then DOB)
                        first_name = result.group(2).strip()
                        last_name = result.group(3).strip()
                        patient_name = f"{first_name}-{last_name}"
                        patient_drug = result.group(1).strip().split(" ")[0]
                        patient_dob = result.group(4).strip().replace("/", "-")
        
        case "Clover Health" | "CVS Caremark":
            patient_name_match = re.search(r'Member Name:\s*([A-Za-z\s\-]+)\s+Member', text)
            patient_drug_match = re.search(r'prescription drug\(s\):\s*\n*\s*([A-Z][A-Z0-9]+)', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1)
        
        case "UnitedHealthcare":
            patient_name_match = re.search(r'Member Name_ \| ([A-Za-z]+(?: [A-Za-z]+)+)', text) or re.search(r'Patient:\s*([A-Za-z\s\-]+)\s+Case', text)
            patient_dob_match = re.search(r'Member DOB (\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'Drug Name (.+?) Approval', text) or re.search(r'inform you that the (.+?) requested', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "Express Scripts":
            name_patterns = [
                r'Patient:\s*([A-Za-z\s\-]+)\s+Physician',
                r'Memver name:\s*([A-Za-z\s\-]+)\s+Member',
                r'Member name:\s*([A-Za-z\s\-]+)\s+Member',
            ]
            # loop over patterns for patient name within express script insurance
            for pattern in name_patterns:
                patient_name_match = re.search(pattern, text)
                if patient_name_match:
                    patient_name = patient_name_match.group(1).strip().replace(" ", "-")
                    break
            
            patient_dob_match = re.search(r'Patient DOB: (\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'request for your patient to obtain coverage for (.+?) under', text) or re.search(r'your request for (.+?) has', text)
            
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "WellCare":
            patient_name_match = re.search(r'Dear\s+([A-Z][a-z]+(?:[-\s][A-Z]?[a-z]+)*):', text)
            patient_drug_match = re.search(r'request from you or your doctor for (.+?)\.', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "Aetna":
            pass

    return patient_name, patient_dob, patient_drug

def find_denial_entitied(text, insurance):
    """
    Based on the extracted ocr text and insurnace type from determine_insurance, get the patient info.
    For each insurance there is its own regex for patient info.
    """

    patient_name = None
    patient_dob = None
    patient_drug = None

    match insurance:
        case "Fidelis Care":
            patient_name_match = re.search(r'Member:\s*([A-Za-z\s\-]+)\s+1D', text) or re.search(r'Member:\s*([A-Za-z\s\-]+)\s+ID', text)
            patient_dob_match = re.search(r'DOB:\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'Question:\s*\n*\s*([A-Z][A-Z0-9]+)', text) or re.search(r'Service:\s*\n*\s*([A-Z][A-Z0-9]+)', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1)

        case "Aetna":
            patient_name_match = re.search(r'Re:\s*([A-Za-z\s\-]+)\s+DOB', text)
            patient_dob_match = re.search(r'DOB:\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'request for coverage of (.+?) for you', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "Horizon":
            patient_name_match = re.search(r'Dear\s+([A-Z\s\-]+):', text)
            patient_dob_match = re.search(r'Date of Birth:\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'request for (.+?) services', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

            # extra case
            if not patient_name and not patient_dob:
                match = re.search(r"RE:\s*([A-Z]+\s+[A-Z]+)\s+(\d{2}/\d{2}/\d{4})", text)
                patient_drug_match = re.search(r'authorization for (.+?). If', text)
                if match:
                    patient_name = match.group(1)
                    patient_dob = match.group(2)
                if patient_drug_match:
                    patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "CVS Caremark":
            patient_name_match = re.search(r'Dear\s+([A-Z\s\-]+):', text)
            patient_drug_match = re.search(r'request for coverage of (.+?) Dear', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "Prime Therapeutics":
            patient_name_match = re.search(r'regarding:\s+([A-Z\s\-]+)\sDrug', text)
            patient_dob_match = re.search(r'Requested:\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'Drug: (.+?) Date', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

    return patient_name, patient_dob, patient_drug


def merge_boxes(boxes, overlap_thresh=30):
    merged = []
    while boxes:
        base = boxes.pop(0)
        bx, by, bw, bh = base
        base_rect = [bx, by, bx + bw, by + bh]
        to_merge = []
        for i, (x, y, w, h) in enumerate(boxes):
            rect = [x, y, x + w, y + h]
            # Check if rectangles are overlapping or close (horizontal + vertical threshold)
            if not (rect[2] < base_rect[0] - overlap_thresh or
                    rect[0] > base_rect[2] + overlap_thresh or
                    rect[3] < base_rect[1] - overlap_thresh or
                    rect[1] > base_rect[3] + overlap_thresh):
                to_merge.append(i)
                base_rect = [
                    min(base_rect[0], rect[0]),
                    min(base_rect[1], rect[1]),
                    max(base_rect[2], rect[2]),
                    max(base_rect[3], rect[3])
                ]
        # Remove merged boxes from list
        for index in sorted(to_merge, reverse=True):
            boxes.pop(index)
        # Append merged box
        merged.append((
            base_rect[0],
            base_rect[1],
            base_rect[2] - base_rect[0],
            base_rect[3] - base_rect[1]
        ))
    return merged

all_results = []

def analyze_and_extract(file_path, file=None):
    pages = convert_from_path(file_path, poppler_path="C:\\Users\\OFFICE\\Documents\\poppler-24.08.0\\Library\\bin", dpi=300) 

    result = []

    # iterate over tha pages sava the page as image
    for i, page in enumerate(pages):
        page.save(f'./debug/images/page_{i}.jpg', 'JPEG')

        # read an image with cv2
        image = cv2.imread(f'./debug/images/page_{i}.jpg')

        # gray the image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # blur an image
        blur = cv2.GaussianBlur(gray, (7,7), 0)

        # threshold image
        # thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        adaptive_tresh_rev = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 5)
        adaptive_tresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 23, 5)
        # cv2.imshow("thresh", cv2.resize(thresh, (560, 900)))
        # cv2.imshow("adaptive_tresh", cv2.resize(adaptive_tresh, (560, 900)))
        # cv2.imshow("original", cv2.resize(image, (560, 900)))
        
        # create an individual kernals
        kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (3,80))

        # dilate image
        dilate = cv2.dilate(adaptive_tresh_rev, kernal, iterations=1)
        cv2.imwrite(f'./debug/images/page_dilate_{i}.jpg', dilate)

        # create contours
        cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        boxes = [cv2.boundingRect(c) for c in cnts]
        boxes = sorted(boxes, key=lambda x: x[0])
        merged_boxes = merge_boxes(boxes)


        for x, y, w, h in merged_boxes:
            if h > 200 and w > 200:
                roi = adaptive_tresh[y:y+h, x:x+w]
                # cv2.rectangle color parameter is BGR
                cv2.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 1)
                ocr_result = pytesseract.image_to_string(roi)
                ocr_result = ocr_result.replace("\n", " ")
                # print(ocr_result)
                result.append(ocr_result) if ocr_result not in result else None

        cv2.imwrite(f'./debug/images/page_boxes_{i}.jpg', image)

    letter_type = None
    insurance = None


    # print(" ".join(result))

    try:
        for filename in os.listdir(os.path.join(os.getcwd(), "debug\\images")):
            file_path = os.path.join(os.path.join(os.getcwd(), "debug\\images"), filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file - {e}")
            
    for entity in result:
        letter_type = determine_letter_type(entity)
        if letter_type:
            break

    for entity in result:
        insurance = determine_insurance(entity)
        if insurance:
            break

    file_result = {
        "file_name": file,
        "letter_type": letter_type,
        "insurance": insurance,
        "ocr_text": result,
        "extracted_entities": None
    }

    if letter_type and insurance:
        print(f"Letter type: {letter_type}\nInsurance: {insurance}")
        match letter_type:
            case "Approval":
                file_result["extracted_entities"] = find_approval_entities(text=" ".join(result), insurance=insurance)
            case "Denial":
                file_result["extracted_entities"] =find_denial_entitied(text=" ".join(result), insurance=insurance)

    if not letter_type:
        letter_type = "Other"

    all_results.append(file_result)

def get_token(username: str, password: str):
    url ="https://api.weaveconnect.com/auth-api/v3/auth/verify"

    payload = {
        "data": {
            "credentials": {
                "username": username,
                "password": password
            }
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"Error while requesting the token: {e}")

    if response.status_code == 200:
        return response.json().get('token')
    else:
        print(f"Error while tried to get token. Status code: {response.status_code}")

def validate_token(token, url, location):
    return requests.get(url, headers={
        "authorization": f"Bearer {token}",
        "location-id": location
    }).status_code

def copy_and_rename_pdf(src_path: str, file_result: dict, dest_root: str, file_name: str):
    """
    Copy the PDF at src_path into a subfolder of dest_root named for its letter_type,
    and rename it to include letter_type, patient_name, dob, and drug,
    replacing any None with 'Unknown'. If file already exists in the folder (ex: with 'Unknown', then add to the name a fax_id - file_name).
    """
    # pull out and normalize each component, defaulting to 'Unknown'
    lt = (file_result.get("letter_type") or "Unknown").replace(" ", "-")
    ins = (file_result.get("insurance") or "Unknown").replace(" ", "-")
    
    # unpack extracted_entities tuple if present
    name, dob, drug = ("Unknown", "Unknown", "Unknown")
    if file_result.get("extracted_entities"):
        ent = file_result["extracted_entities"]
        name = (ent[0] or "Unknown").replace(" ", "-")
        dob  = (ent[1] or "Unknown").replace(" ", "-")
        drug = (ent[2] or "Unknown").replace(" ", "-")
    
    # build destination directory and filename
    dest_dir = os.path.join(dest_root, lt)
    os.makedirs(dest_dir, exist_ok=True)
    new_fname = f"{lt}_{name}_{dob}_{drug}.pdf"
    dest_path = os.path.join(dest_dir, new_fname)

    # check if the file already exists in the directory
    if os.path.exists(dest_path):
        new_fname = f"{lt}_{name}_{dob}_{drug}_{file_name}.pdf"
        dest_path = os.path.join(dest_dir, new_fname)
    
    # copy
    shutil.copyfile(src_path, dest_path)

def main(file=None):

    start_time = time.perf_counter()

    date = (datetime.now() - timedelta(days=1)).strftime("%m-%d-%Y")
    faxurl = f"{os.getenv("URL_REQUEST")}?recipient=&sender=&start={date}&end={date}"

    # Getting token and validating it
    try:
        token = get_token(
                username=os.getenv("USERNAME_ENV"),
                password=os.getenv("PASSWORD_ENV")
            )
        
        # print("\n\n", token, "\n\n")
        if (token):
            status = validate_token(
                    url=faxurl,
                    token=token,
                    location=os.getenv("LOCATION_ID")
                )
            if (status != 200):
                print(f"Token is not validated. Status code: {status}")
                return 0
    except Exception as e:
        print(f"Error: {e}")

    # make folder for the dedicated date
    date_location = f"{os.getcwd()}\\debug\\{date}"
    if(not os.path.exists(date_location)):
        os.mkdir(date_location)

    filepath = f"{date_location}\\dump-{date}.json"

    if (os.path.exists(filepath)):
        print(f"Json for the {date} already exists in {date_location}")
    else:
    # getting and saving faxes info into json 
        try:
            response = requests.get(faxurl, headers={
                'Authorization' : f'Bearer {token}',
                'Location-id': location,
            })

            if (response.ok):
                # new_json = os.open(f'{filepath}\\dump.json', 'x')
                with open(filepath, 'w') as f:
                    json.dump(response.json(), f, indent=4)
                print(f"Data successfully written to {filepath}")
            else:
                print(response.text)
        except Exception as e:
            print(f"Error getting response: {e}")

    with open (f"{date_location}\\dump-{date}.json", "r") as file:
        data = json.load(file)
        count = 0
        for i, item in enumerate(data["data"]):
            pdf_id = item.get("ID")
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
                continue

            pdf_dump_dir = os.path.join(date_location, "pdf_dump")
            if not os.path.exists(pdf_dump_dir):
                os.mkdir(pdf_dump_dir)

            temp_pdf_path = os.path.join(pdf_dump_dir, f"pdf-{pdf_id}.pdf")
            with open(temp_pdf_path, 'wb') as pdf_file:
                pdf_file.write(response.content)

            if os.path.exists(temp_pdf_path):
                analyze_and_extract(file_path=temp_pdf_path, file=pdf_id)
                # os.remove(temp_pdf_path)
                copy_and_rename_pdf(
                        src_path=temp_pdf_path,
                        file_result=all_results[-1],
                        dest_root=date_location,
                        file_name=pdf_id
                    )
    
            count += 1

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)

    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print (f"Program ran in {execution_time/60:.2f} minutes\nFinished - {count} letters")


if __name__ == "__main__":
    main()
        


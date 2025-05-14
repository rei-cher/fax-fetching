import cv2, pytesseract, re, os, json, time
from pdf2image import convert_from_path

path = "C:\\Users\\OFFICE\\Documents\\dump\\05-13-2025"

pytesseract.pytesseract.tesseract_cmd = "C:\\Users\\OFFICE\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"
        

insurance_types = [
    "Healthfirst",
    "Wellpoint",
    "Fidelis Care",
    "HORIZON",
    "Prime Therapeutics",    # Private horizon
    "Clover Health",
    "UnitedHealthcare",    # UnitedHealthCare
    "Express Scripts",
    "WellCare",
    "Aetna",
    "Horizon"
]

approval_patterns = [
    r"\bhas been approved\b",
    r"\bType of coverage approved: Prior Authorization\b",
    r"\bType of coverage approved: Non-Formulary\b",
    r"\bpproved for\b",
    r"\bThis drug has been approved\b",
    r"\bThis request has been reviewed and approved for the following time period\b",
    r"\bApproved for\b",
    r"\bapproved the requast as follows\b",
    r"\bthe request is approved for the following time period\b",
    r"\bwriting to let you know that we have approved\b",
    r"\bAPPROVAL NOTICE\b",
]

# TODO: adjust denial letter patters 
denial_patterns = [
    r"Reason for Denial:",
    r"__X__ Denying your request for",
    r"__X__Denying your request for",
    r"RE: Denial of request for coverage",
    r"denied the request for the following reason",
    r"We are unable to approve your request for this drug",
]

def determine_letter_type(text):
    for pattern in approval_patterns:
        if re.search(pattern, text):
            return "Approval"
    for pattern in denial_patterns:
        if re.search(pattern, text):
            return "Denial"

def determine_insurance(text):
    """
    From the extracted ocr text, matching the words with the list of pre-exist insurances.
    If there is a match, returns the name of the insurance.
    """
    return next((insurance for insurance in insurance_types if insurance in text), None)


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
        
        case "HORIZON":
            pattern = re.search(r'has requested\s+([A-Za-z\s]+?)\s+for\s+([A-Z\s]+?),\s*ID\s*#\s*\d+,\s*DOB\s*(\d{1,2}/\d{1,2}/\d{4})', text, re.DOTALL)
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
        
        case "Clover Health":
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
            patient_name_match = re.search(r'Patient:\s*([A-Za-z\s\-]+)\s+Physician', text) or re.search(r'Memver name:\s*([A-Za-z\s\-]+)\s+Member', text)
            patient_dob_match = re.search(r'Patient DOB: (\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'request for your patient to obtain coverage for (.+?) under', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "WellCare":
            patient_name_match = re.search(r'Dear\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):', text)
            patient_drug_match = re.search(r'request from you or your doctor for (.+?)\.', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

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
count = 0
start_time = time.perf_counter()
for root, dirs, files in os.walk(path):
    for file in files:
        if not file.lower().endswith(".pdf"):
            continue

        file_path = os.path.join(root, file)
        print(file_path)
        # since the pdf is not an image, we have to convert each page into the image
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
                print("Letter type recognized - ", letter_type)
                break

        for entity in result:
            insurance = determine_insurance(entity)
            if insurance:
                print("Insurance type recognized - ", insurance)
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

            all_results.append(file_result)

        count += 1

with open("results.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=4)

end_time = time.perf_counter()
execution_time = end_time - start_time
print (f"Program ran in {execution_time/60:.2f} minutes\nFinished - {count} letters")
        


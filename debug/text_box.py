import cv2, pytesseract, re
from pdf2image import convert_from_path

name = "Approval_ANTONIA-FRENCH_n-a_OPZELURA"  # Healthfirst approval
# name = "Approval_Angelin-Samuel_01-20-2014_ADAPALENE"   # Wellpoint approval
# name = "Approval_Bryan-Bhagwandat _09-04-2006_CLOBETASOL"   # Fideli care approval
# name = "Approval_CRISTIA-HERNANDEZ_3-12-2010_Doxycycline"   # Horizon approval
# name = "Approval_NALINI-AJODHA_2-11-1969_TACROLIMUS"    # Prime Therapeutics - private horizon
# name = "Approval_RAMONA-ROSA-ROSARIO_1-27-1945_TACROLIMUS"  # TODO: currently doesnt work
# name = "Approval_SANTA-BAEZ_11-05-1975_COSENTYX"
# name = "Approval_Danny-Virovlyansky_n-a_ISOTRETINOIN"
pdf = f"C:\\Users\\OFFICE\\Documents\\dump\\05-09-2025\\approvals\\{name}.pdf"
pytesseract.pytesseract.tesseract_cmd = "C:\\Users\\OFFICE\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"

# since the pdf is not an image, we have to convert each page into the image
pages = convert_from_path(pdf, poppler_path="C:\\Users\\OFFICE\\Documents\\poppler-24.08.0\\Library\\bin", dpi=300) 

insurance_types = [
    "Healthfirst",
    "Wellpoint",
    "Fidelis Care",
    "HORIZON",
    "Prime Therapeutics"    # Private horizon
]

approval_patterns = [
    r"\bhas been approved\b",
    r"\bType of coverage approved: Prior Authorization\b",
    r"\bType of coverage approved: Non-Formulary\b",
    r"\bpproved for\b",
    r"\bThis drug has been approved\b",
    r"\bThis request has been reviewed and approved for the following time period\b",
    r"\bApproved for\b",
]

denial_patterns = [
    r"\byour request has been denied\b",
    r"\byour request was denied for the following reason\b",
    r"\bthe prior authorization is denied\b",
    r"\bwe have denied\b",
    r"\bwe have rejected\b",
    r"\bnot covered\b",
    r"\bx denying your request for\b",
    r"\bwe are not approving this medication because\b",
    r"\bthis is the reason for the denial\b",
]

def determine_letter_type(text):
    for pattern in approval_patterns:
        if re.search(pattern, text):
            return "Approval"
    for pattern in denial_patterns:
        if re.search(pattern, text):
            return "Denial"
    return "Unknown"

def determine_insurance(text):
    """
    From the extracted ocr text, matching the words with the list of pre-exist insurances.
    If there is a match, returns the name of the insurance.
    """
    return next((insurance for insurance in insurance_types if insurance in text), None)

def find_entities(text, insurance):
    """
    Based on the extracted ocr text and insurnace type from determine_insurance, get the patient info.
    For each insurance there is its own regex for patient info.
    """

    patient_name = "Unknown"
    patient_dob = "Unknown"
    patient_drug = "Unknown"

    match insurance:
        case "Healthfirst":
            patient_name_match = re.search(r'Member Name:\s*(.*?)\s+Member\b', text)
            patient_drug_match = re.search(r'drug\(s\):\s*\n*\s*([A-Z][A-Z0-9]+)', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
                patient_drug = patient_drug_match.group(1)
                # print(f"Patient name: {patient_name}")
                # print(f"Patient drug: {patient_drug}")

        case "Wellpoint":
            patient_info_match = re.search(r'Member:\s*\d+,\s*([A-Za-z\s]+),\s*(\d{2}/\d{2}/\d{4})', text)
            patient_drug_match = re.search(r'follows:\s*\n*\s*([A-Z][A-Z0-9]+)', text)
            if patient_info_match:
                patient_name = patient_info_match.group(1).strip().replace(" ", "-")
                patient_dob = patient_info_match.group(2).replace("/", "-")
                # print(f"Patient name: {patient_name}")
                # print(f"Patient dob: {patient_dob}")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1)
                # print(f"Patient drug: {patient_drug}")

        case "Fidelis Care":
            patient_name_match = re.search(r'Member:\s*([A-Za-z\s\-]+)\s+ID', text) or re.search(r'Member Name:\s*([A-Za-z\s\-]+)\s+Member', text)
            patient_dob_match = re.search(r'DOB:\s*(\d{2}/\d{2}/\d{4})', text)
            patient_drug_match = re.search(r'Question:\s*\n*\s*([A-Z][A-Z0-9]+)', text) or re.search(r'Service:\s*\n*\s*([A-Z][A-Z0-9]+)', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
                # print(f"Patient name: {patient_name}")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
                # print(f"Patient dob: {patient_dob}")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1)
                # print(f"Patient drug: {patient_drug}")
        
        case "HORIZON":
            pattern = re.search(r'has requested\s+([A-Za-z\s]+?)\s+for\s+([A-Z\s]+?),\s*ID\s*#\s*\d+,\s*DOB\s*([0-9/]+)', text, re.DOTALL)
            if pattern:
                patient_name = pattern.group(2).replace('\n', ' ').strip().replace(" ", "-")
                # print(f"Patient name: {patient_name}")
                patient_dob = pattern.group(3).strip().replace("/", "-")
                # print(f"Patient dob: {patient_dob}")
                patient_drug = pattern.group(1).strip().split(" ")[0]
                # print(f"Patient drug: {patient_drug}")
        
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
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # create an individual kernals
    kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (3,80))

    # dilate image
    dilate = cv2.dilate(thresh, kernal, iterations=2)
    # cv2.imwrite(f'./debug/images/page_dilate_{i}.jpg', dilate)

    # create contours
    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    boxes = [cv2.boundingRect(c) for c in cnts]
    boxes = sorted(boxes, key=lambda x: x[0])
    merged_boxes = merge_boxes(boxes)

    insurance = ""
    result = []
    for x, y, w, h in merged_boxes:
        if h > 200 and w > 200:
            roi = image[y:y+h, x:x+w]
            # cv2.rectangle color parameter is BGR
            cv2.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 1)
            ocr_result = pytesseract.image_to_string(roi)
            ocr_result = ocr_result.replace("\n", " ")
            # print(ocr_result)
            result.append(ocr_result) if ocr_result not in result else None
            
    for entity in result:
        letter_type = determine_letter_type(entity)
        insurance = determine_insurance(entity)
        if insurance and letter_type:
            print(f"Letter type is: {letter_type}")
            print(f"Insurance is: {insurance}")
            break

    # if insurance:
    #     for entiry in result:
    #         print(find_entities(entiry, insurance))

    # print(result)

    cv2.imwrite(f'./debug/images/page_boxes_{i}.jpg', image)


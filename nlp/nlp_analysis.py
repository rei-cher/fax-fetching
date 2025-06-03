import cv2, pytesseract, os, json
from pdf2image import convert_from_path
from .text_analyzation import find_approval_entities, find_denial_entities, find_request_entities
from .letter_type import determine_letter_type
from .insurance_type import determine_insurance

results = []

# helper function to merge small boxes into a bigger
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

def delete_images(images_path):
    for filename in os.listdir(images_path):
            file_path = os.path.join(images_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

def analyze_and_extract(file_path, poppler_path, file, pytesseract_path) -> dict:

    pytesseract.pytesseract.tesseract_cmd = pytesseract_path
    pages = convert_from_path(file_path, poppler_path=poppler_path, dpi=300) 

    images_path = os.path.join(os.getcwd(), 'images')
    result = []

    if not os.path.exists(images_path):
        os.mkdir(images_path)

    # iterate over tha pages sava the page as image
    for i, page in enumerate(pages):
        page.save(f'{images_path}/page_{i}.jpg', 'JPEG')

        # read an image with cv2
        image = cv2.imread(f'{images_path}/page_{i}.jpg')

        # gray the image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # blur an image
        blur = cv2.GaussianBlur(gray, (7,7), 0)

        # threshold image
        adaptive_tresh_rev = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 5)
        adaptive_tresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 23, 5)
        
        # create an individual kernals
        kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (3,80))

        # dilate image
        dilate = cv2.dilate(adaptive_tresh_rev, kernal, iterations=1)
        # cv2.imwrite(f'{images_path}/page_dilate_{i}.jpg', dilate)

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

        # cv2.imwrite(f'{images_path}/page_boxes_{i}.jpg', image)

    letter_type = None
    insurance = None


    # print(" ".join(result))

    try:
        delete_images(images_path=images_path)
    except Exception as e:
        print(f"Error deleting file - {e}")
            
    for entity in result:
        letter_type = determine_letter_type(entity)
        if letter_type:
            break
        else:
            letter_type = "Other"

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

    if letter_type != "Other" and insurance:
        # print(f"Letter type: {letter_type}\nInsurance: {insurance}")

        # ==== Uncomment to get the json logs for the approval and denials faxes ====
        # results.append(file_result)

        # with open("approvals_denials_results.json", "w") as file:
        #     json.dump(results, file, indent=4)

        match letter_type:
            case "Approval":
                file_result["extracted_entities"] = find_approval_entities(text=" ".join(result), insurance=insurance)
            case "Denial":
                file_result["extracted_entities"] = find_denial_entities(text=" ".join(result), insurance=insurance)
            case "PA-Request":
                file_result["extracted_entities"] = find_request_entities(text=" ".join(result))

    return file_result

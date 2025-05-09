import cv2, pytesseract
from pdf2image import convert_from_path

name = "Approval_DAVID-ELDRIDGE_3-6-1989_EUCRISA"
pdf = f"D:\\faxes\\dates\\05-08-2025\\approvals\\{name}.pdf"
pytesseract.pytesseract.tesseract_cmd = "C:\\Users\\OFFICE\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"

# since the pdf is not an image, we have to convert each page into the image
pages = convert_from_path(pdf, poppler_path="C:\\Users\\OFFICE\\Documents\\poppler-24.08.0\\Library\\bin", dpi=300) 

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
    kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (3,13))

    # dilate image
    dilate = cv2.dilate(thresh, kernal, iterations=2)
    cv2.imwrite(f'./debug/images/page_dilate_{i}.jpg', dilate)

    # create contours
    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    boxes = [cv2.boundingRect(c) for c in cnts]
    boxes = sorted(boxes, key=lambda x: x[0])
    merged_boxes = merge_boxes(boxes)

    for x, y, w, h in merged_boxes:
        if h > 43 and w > 70:
            roi = image[y:y+h, x:x+w]
            # cv2.rectangle color parameter is BGR
            cv2.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 1)
            ocr_result = pytesseract.image_to_string(roi)
            print(ocr_result)

    cv2.imwrite(f'./debug/images/page_boxes_{i}.jpg', image)
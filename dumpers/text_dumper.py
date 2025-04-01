from async_functions.async_fetch import fetch_and_analyze_async

def text_extracting(url, token, location, path, date, poppler_path, tesseract_path):
    fetch_and_analyze_async(
        url=url,
        token=token,
        location=location,
        path=path,
        date=date,
        poppler_path=poppler_path,
        tesseract_path=tesseract_path
    )

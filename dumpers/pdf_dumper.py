import requests, time

def download_pdf(pdf_url, token, location):
    """
    Download pdf accepting the following parameters:
        pdf_url: url of exact fax id
        token: authorization token (gets after login response)
        location: location id of the organization (stored in .env)
    """
    try:
        response = requests.get(
            pdf_url,
            headers={
                "content-type": "application/pdf",
                'Authorization' : f'Bearer {token}',
                'Location-id': location,
            }
        )

        return response
    except requests.exceptions.ConnectionError:
        print(f"Download of {pdf_url.split("/")[-1]} failed due to exceed of requests\nWaiting 20 seconds, then retrying.")
        time.sleep(20)
        response = requests.get(
            pdf_url, 
            headers={
                "content-type": "application/pdf",
                'Authorization' : f'Bearer {token}',
                'Location-id': location,
            }
        )
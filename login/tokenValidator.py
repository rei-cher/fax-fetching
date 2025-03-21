import requests

def validate_token(token, url, location):
    return requests.get(url, headers={
        "authorization": f"Bearer {token}",
        "location-id": location
    }).status_code
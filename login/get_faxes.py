import requests

def get_last_faxes(token: str):
    url = f"https://api.weaveconnect.com/fax/v1/faxes?locationId=77f850f9-6d12-4278-8b93-8bc390422dfe&locationIds=77f850f9-6d12-4278-8b93-8bc390422dfe"

    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "location-id": "77f850f9-6d12-4278-8b93-8bc390422dfe"
    }

    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        print(f"Error while requesting the token: {e}")

    if response.status_code == 200:
        return response
    else:
        print(f"Error while tried to get last faxes. Status code: {response.status_code}")
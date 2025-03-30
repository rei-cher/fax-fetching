import requests

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

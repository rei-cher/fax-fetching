import os
import mimetypes
import requests

def authenticate(hostname, client_id, client_secret, username, password):
    """Authenticate via password grant. Returns JSON token object."""
    if not hostname.startswith("https://"):
        hostname = "https://" + hostname
    uri = f"{hostname}/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
    }
    response = requests.post(uri, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_authorization_header(token):
    return {"Authorization": f"Bearer {token['access_token']}"}

def get_hostname(token: dict) -> str:
    return f"{token['subdomain']}.sharefile.com"

def get_root(token: dict, get_children: bool = True) -> list:
    """Return the top‐level 'allshared' children."""
    uri = "/sf/v3/Items(allshared)"
    if get_children:
        uri += "?$expand=Children"
    hostname = get_hostname(token)
    url = f"https://{hostname}{uri}"
    headers = get_authorization_header(token)
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json().get("Children", [])

def get_folder_with_query_parameters(token: dict, item_id: str) -> dict:
    """Fetch a specific item with its children expanded."""
    hostname = get_hostname(token)
    url = f"https://{hostname}/sf/v3/Items({item_id})"
    params = {
        "$expand": "Children",
        "$select": "Id,Name,Children/Id,Children/Name,Children/CreationDate"
    }
    headers = get_authorization_header(token)
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()

def create_folder(token: dict, parent_id: str, name: str, description: str = "") -> dict:
    """Create a new subfolder under parent_id."""
    hostname = get_hostname(token)
    url = f"https://{hostname}/sf/v3/Items({parent_id})/Folder"
    headers = get_authorization_header(token)
    headers["Content-Type"] = "application/json"
    payload = {"Name": name, "Description": description}
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()

def get_today_folder(token: dict, date: str) -> str:
    """
    Under root 'FAXES', find or create a folder named `date`.
    Returns its Id.
    """
    # locate FAXES
    for item in get_root(token):
        if item.get("Name") == "FAXES":
            faxes_id = item["Id"]
            break
    else:
        raise RuntimeError("Root folder 'FAXES' not found")

    # check for existing date folder
    data = get_folder_with_query_parameters(token, faxes_id)
    for child in data.get("Children", []):
        if child.get("Name") == date:
            return child["Id"]

    # create it if missing
    new = create_folder(token, faxes_id, date, "")
    return new["Id"]

def ensure_folder(token: dict, parent_id: str, name: str) -> str:
    """
    Under parent_id, find or create a subfolder named `name`.
    Returns its Id.
    """
    data = get_folder_with_query_parameters(token, parent_id)
    for child in data.get("Children", []):
        if child.get("Name") == name:
            return child["Id"]
    new = create_folder(token, parent_id, name, "")
    return new["Id"]

def upload_file(token: dict, folder_id: str, local_path: str, remote_name: str = None) -> requests.Response:
    """
    Uploads `local_path` into the ShareFile folder `folder_id`.
    If `remote_name` is set, the file will be named accordingly.
    """
    hostname = get_hostname(token)
    uri = f"https://{hostname}/sf/v3/Items({folder_id})/Upload"
    headers = get_authorization_header(token)

    # 1) get chunk URL
    resp = requests.get(uri, headers=headers)
    resp.raise_for_status()
    chunk_uri = resp.json().get("ChunkUri")
    if not chunk_uri:
        raise RuntimeError("No ChunkUri received for upload")

    # 2) POST the file
    filename = remote_name or os.path.basename(local_path)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    with open(local_path, "rb") as f:
        files = {"File1": (filename, f, content_type)}
        upload_resp = requests.post(chunk_uri, files=files)
    upload_resp.raise_for_status()
    return upload_resp

import os
import mimetypes
import requests

def authenticate(hostname, client_id, client_secret, username, password):
    """Authenticate via authorization_code. Returns JSON token object."""
    
    # Ensure hostname has https://
    if not hostname.startswith("https://"):
        hostname = "https://" + hostname

    uri_path = f'{hostname}/oauth/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    data = {
        'grant_type': 'password',
        'client_id': client_id,
        'client_secret': client_secret,
        'username': username,
        'password': password
    }

    response = requests.post(uri_path, headers=headers, data=data)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code, response.text)
        return None

def get_authorization_header(token):
    return {'Authorization': f"Bearer {token['access_token']}"}

def get_hostname(token: dict) -> str:
    return f"{token['subdomain']}.sharefile.com"

def upload_file(token: dict, folder_id: str, local_path: str):
    """
    Uploads a file to a ShareFile folder using the ShareFile REST API and multipart/form-data.
    Uses the requests library.
    """
    hostname = get_hostname(token)
    uri = f"https://{hostname}/sf/v3/Items({folder_id})/Upload"

    headers = get_authorization_header(token)
    print('GET', uri)

    response = requests.get(uri, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"Failed to get upload URL: {response.status_code} - {response.text}")

    upload_config = response.json()
    chunk_uri = upload_config.get("ChunkUri")

    if not chunk_uri:
        print("No Upload URL received")
        return

    # Upload file using requests
    upload_response = multipart_form_post_upload(chunk_uri, local_path)
    print(upload_response.status_code, upload_response.reason)
    print(upload_response.text)


def multipart_form_post_upload(url: str, filepath: str) -> requests.Response:
    """
    Handles multipart/form-data POST upload using requests.
    """
    filename = os.path.basename(filepath)
    content_type = get_content_type(filename)

    with open(filepath, 'rb') as f:
        files = {
            'File1': (filename, f, content_type)
        }
        response = requests.post(url, files=files)

    return response

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def get_root(token: dict, get_children: bool = True) -> dict:
    """
    Get the root-level Item (allshared) for the authenticated ShareFile user.
    
    Args:
        token (dict): Token object from the authenticate() function.
        get_children (bool): Whether to retrieve child items (folders/files).
    
    Returns:
        dict: Parsed JSON response containing root item metadata and children if requested.
    """
    uri_path = '/sf/v3/Items(allshared)'
    if get_children:
        uri_path += '?$expand=Children'

    hostname = get_hostname(token)
    url = f'https://{hostname}{uri_path}'
    headers = get_authorization_header(token)

    print('GET', url)
    response = requests.get(url, headers=headers)

    print(response.status_code, response.reason)

    if response.status_code != 200:
        raise RuntimeError(f"Request failed with status {response.status_code}: {response.reason}")

    items = response.json()
    return items.get('Children')

    # print(items.get('Id'), items.get('CreationDate'), items.get('Name'))

    # if 'Children' in items:
    #     for child in items['Children']:
    #         print(child.get('Id'), child.get('CreationDate'), child.get('Name'))

    # return items

def get_folder_with_query_parameters(token: dict, item_id: str) -> dict:
    """
    Retrieves a folder and its children using ShareFile query parameters:
    - $expand=Children to include child items
    - $select=Id,Name,Children/Id,Children/Name,Children/CreationDate to limit fields

    Args:
        token (dict): Authentication token
        item_id (str): Folder ID

    Returns:
        dict: Folder metadata with child folders (if any)
    """
    hostname = get_hostname(token)
    url = f"https://{hostname}/sf/v3/Items({item_id})"
    params = {
        '$expand': 'Children',
        '$select': 'Id,Name,Children/Id,Children/Name,Children/CreationDate'
    }

    headers = get_authorization_header(token)
    print(f'GET {url} with params {params}')
    
    response = requests.get(url, headers=headers, params=params)
    print(response.status_code, response.reason)

    if response.status_code != 200:
        raise RuntimeError(f"Failed to get folder info: {response.status_code} - {response.text}")

    data = response.json()

    # print(data.get('Id'), data.get('Name'))

    # if 'Children' in data:
    #     for child in data['Children']:
    #         print(child['Name'])

    return data

def create_folder(token, parent_id, name, description):
    """Create a new folder in the given parent folder.

    Args:
        dict token: JSON token acquired from authenticate function
        str parent_id: The parent folder in which to create the new folder
        str name: The folder name
        str description: The folder description
    """
    uri_path = f'/sf/v3/Items({parent_id})/Folder'
    base_url = get_hostname(token)
    url = f'https://{base_url}{uri_path}'

    print(f'POST {url}')

    folder = {
        'Name': name,
        'Description': description
    }

    headers = get_authorization_header(token)
    headers['Content-Type'] = 'application/json'

    response = requests.post(url, headers=headers, json=folder)

    print(response.status_code, response.reason)

    if response.ok:
        new_folder = response.json()
        print(f'Created Folder {new_folder["Id"]}')
        return new_folder
    else:
        print(f'Error creating folder: {response.text}')
        response.raise_for_status()
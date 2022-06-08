import os
import shutil
import dropbox
import requests
import platform
from . import header
from .dropboxhasher import DropboxContentHasher


# OS info
OS_TYPE = platform.system().lower()
ARCH_TYPE = platform.architecture()[0].lower()
CLOUD_DIR = '/%s/%s' % (OS_TYPE, ARCH_TYPE)


def __checksum(path: str) -> str:
    algorithm = DropboxContentHasher()

    with open(path, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            algorithm.update(chunk)

    return algorithm.hexdigest()


def __get_files() -> list:
    client = dropbox.Dropbox(oauth2_access_token=header.ACCESS_TOKEN, timeout=None)
    result = []

    try:
        maximum_limit = 2000
        for file in client.files_list_folder(CLOUD_DIR, recursive=True, limit=maximum_limit).entries:
            if file.path_lower != CLOUD_DIR:
                result.append(file)
    except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError):
        pass
    finally:
        client.close()
        return result


def download():
    files = __get_files()
    client = dropbox.Dropbox(oauth2_access_token=header.ACCESS_TOKEN, timeout=None)
    os.makedirs(header.UPDATE_DIR, exist_ok=True)

    for file in files:
        if not isinstance(file, dropbox.files.FileMetadata):
            continue

        file_path = os.path.relpath(file.path_display, CLOUD_DIR)
        temp_path = os.path.join(header.UPDATE_DIR, file_path)
        app_path = os.path.join(header.APP_DIR, file_path)
        in_temp = os.path.exists(temp_path) and file.content_hash == __checksum(temp_path)
        in_app = os.path.exists(app_path) and file.content_hash == __checksum(app_path)

        if not in_temp and not in_app:
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            client.files_download_to_file(download_path=temp_path, path=file.id)

    client.close()


def update() -> bool:
    valid = False
    if os.path.exists(header.UPDATE_DIR) and len(os.listdir(header.UPDATE_DIR)) > 0:
        shutil.copytree(header.UPDATE_DIR, header.APP_DIR, dirs_exist_ok=True)
        shutil.rmtree(header.UPDATE_DIR, ignore_errors=True)
        valid = True

    return valid

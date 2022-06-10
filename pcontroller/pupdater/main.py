from . import header
from . import dropboxfunc
from .header import Metadata
import os
import json
import requests


def __fetching(url: str) -> dict:
    try:
        return requests.get(url).json()
    except requests.exceptions.ConnectionError:
        return {}


def set_app_dir(path: str):
    header.APP_DIR = path


def set_api_client(api_url: str):
    header.API_URL = api_url
    header.ACCESS_TOKEN = __fetching(api_url).get(Metadata.accessToken)


def latest_version() -> dict:
    result = {
        Metadata.latestVersion: None, Metadata.title: None, Metadata.description: None
    }

    return __fetching(header.API_URL).get(Metadata.info, result)


def latest_update() -> dict:
    result = {
        Metadata.latestVersion: None, Metadata.title: None, Metadata.description: None
    }

    try:
        with open(os.path.join(header.TEMP_DIR, 'update_cache.json'), 'r') as file:
            data = json.load(file)
            result[Metadata.latestVersion] = data.get(Metadata.latestVersion)
            result[Metadata.title] = data.get(Metadata.title)
            result[Metadata.description] = data.get(Metadata.description)

    except FileNotFoundError:
        pass
    finally:
        return result


def is_updated(default: bool = False) -> bool:
    _latest_version = latest_version()[Metadata.latestVersion]
    _latest_update = latest_update()[Metadata.latestVersion]

    if not _latest_version:
        return default

    return _latest_version == _latest_update


def download() -> bool:
    result = False
    if not is_updated():
        dropboxfunc.download()
        result = True

    return result


def update() -> bool:
    result = dropboxfunc.update()
    if result:
        with open(os.path.join(header.TEMP_DIR, 'update_cache.json'), 'w') as file:
            json.dump(latest_version(), file)

    return result


__all__ = [
    'Metadata', 'set_app_dir', 'set_api_client',
    'latest_version', 'latest_update', 'is_updated', 'download', 'update'
]

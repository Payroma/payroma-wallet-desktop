import os


TEMP_DIR = 'temp'
UPDATE_DIR = os.path.join(TEMP_DIR, 'updates')
APP_DIR = None
API_URL = None
ACCESS_TOKEN = None


class Metadata:
    info = 'info'
    latestVersion = 'latestVersion'
    title = 'title'
    description = 'description'
    accessToken = 'accessToken'

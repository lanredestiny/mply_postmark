import os

import toml

SUPPORTED_LANGUAGES = ['en', 'fr', 'it', 'de']


def get_settings():
    SETTINGS_FILE_PATH = os.environ['MPLY_EML_CONFIG']
    return toml.load(SETTINGS_FILE_PATH)

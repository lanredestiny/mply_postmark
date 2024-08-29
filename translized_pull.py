import os.path
from pprint import pprint
import sys

import requests

from cfg import get_settings, SUPPORTED_LANGUAGES


def _pull(lang, api_key, project_id):
    resp = requests.post(
        'https://api.translized.com/project/export',
        headers={
            'api-token': api_key,
        }, json={
            'projectId': project_id,
            'exportFormat': 'po',
            'languageCode': lang
        })
    resp.raise_for_status()
    res_url = resp.json()['result']['fileURL']
    file_resp = requests.get(res_url)
    file_resp.raise_for_status()
    path = os.path.join(os.path.dirname(__file__),
        'translations/{}/LC_MESSAGES/messages.po'.format(lang))
    with open(path, 'wb') as f:
        f.write(file_resp.content)
    return path


def main():
    cfg = get_settings()
    lang_and_paths = []
    for lang in SUPPORTED_LANGUAGES:
        print("Generating PO file for lang {}".format(lang))
        path = _pull(lang, cfg['TRANSLIZED_API_KEY'],
            cfg['TRANSLIZED_PROJECT_ID'])
        print("Downloaded {0} to translations/{0}/LC_MESSAGES/messages.po".format(lang))
        lang_and_paths.append((lang, path))

    print('done')


if __name__ == '__main__':
    main()

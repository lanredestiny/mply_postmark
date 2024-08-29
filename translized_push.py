import polib
import requests

from cfg import get_settings


def push_pot(pot_fn, po_fn, api_key, project_id):
    potfile = polib.pofile(pot_fn, autodetect_encoding=False, encoding="utf-8", wrapwidth=-1)
    assert isinstance(potfile, polib.POFile)

    remotely_known_keys = set()
    # pofile = polib.pofile(po_fn, encoding="utf-8", wrapwidth=-1)
    # assert isinstance(pofile, polib.POFile)
    #
    # remotely_known_keys = set(e.msgid for e in pofile)
    # remote_empty_keys = set(e.msgid for e in pofile if not e.msgstr)

    # for k in dir(potfile[1]):
    #     if k.startswith('_'):
    #         continue
    #     print k, getattr(potfile[1], k)

    # for po_entry in potfile[:10]:
    # locally_known_keys = set()
    for po_entry in potfile:
        if po_entry.msgid in remotely_known_keys:
            continue
        # locally_known_keys.add(po_entry.msgid)
        resp = requests.post(
            'https://api.translized.com/term/add',
            headers={
                'api-token': api_key,
            }, json={
                'projectId': project_id,
                'termKey': po_entry.msgid,
                'context': u'\n'.join(u'{} {}'.format(l,n) for l,n in po_entry.occurrences)
            })
        if resp.status_code == 400:
            if resp.json()['code'] == 141:
                status = 'DUP'
            else:
                print(resp.json())
                resp.raise_for_status()
        else:
            resp.raise_for_status()
            status = resp.status_code
        print(u'{}: {}'.format(status, po_entry.msgid))

if __name__ == '__main__':
    cfg = get_settings()
    api_key = cfg['TRANSLIZED_API_KEY']
    project_id = cfg['TRANSLIZED_PROJECT_ID']
    push_pot('translations/messages_eml.pot', 'translations/en/LC_MESSAGES/messages.po', api_key, project_id)

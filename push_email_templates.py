# Combine all translated email_templates with their metadata (e.g. title and nickname?)
# then push these to Postmark
import json
import os
import string
from copy import copy

import click
import requests
from rich import print as rich_print

from cfg import SUPPORTED_LANGUAGES, get_settings

BASE_URL = 'https://api.postmarkapp.com'

EMAIL_TEMPLATES_BASE_DIR = './email_templates'

class TemplateError(Exception):
    pass

class TemplateNotFound(TemplateError):
    pass


def get_template_set_metadata(template_set_dir):
    metadata_file_path = os.path.join(template_set_dir, 'metadata.json')
    if not os.path.exists(metadata_file_path):
        raise TemplateError("Missing metadata file %s" % metadata_file_path)

    rich_print(f"Reading metadata from [yellow]{metadata_file_path}[/yellow]")
    with open(metadata_file_path, 'r') as f:
        metadata = json.load(f)

    return metadata

def get_template_file_path(template_set_dir, locale):
    template_base_name = EmailTemplateSet.template_base_name_from_template_set_dir(template_set_dir)
    file_path = os.path.join(template_set_dir, f"{template_base_name}_{locale}.html")
    return file_path

class TemplateCache(object):

    def __init__(self, requests_session):
        self._templates = None
        self.rs = requests_session

    def _list_all_templates(self):
        url = BASE_URL + '/templates'
        limit = 50
        params = {"offset": 0, "count": limit}
        resp = self.rs.get(url, params=params)
        data = resp.json()
        assert (data["TotalCount"] < limit), "Consider changing the limit parameter"  # or implement iteration
        print(data)

        return data['Templates']

    def by_attribute(self, attribute_name, attribute_val, force_refresh=False):
        assert attribute_name in {'Alias', 'TemplateId'}
        templates_are_fresh = False
        if self._templates is None or force_refresh:
            self._templates = self._list_all_templates()
            templates_are_fresh = True
        for t in self._templates:
            if t[attribute_name] == attribute_val:
                return t
        if templates_are_fresh:
            raise TemplateNotFound(f"Could not find template with {attribute_name} = {attribute_val}")

        return self.by_attribute(attribute_name, attribute_val, force_refresh=True)

    def by_alias(self, template_name):
        return self.by_attribute('Alias', template_name)

    def by_id(self, template_id):
        return self.by_attribute('TemplateId', template_id)


class EmailTemplate(object):

    def __init__(self, template_set_dir, locale):
        assert os.path.isdir(template_set_dir)
        assert locale.lower() in SUPPORTED_LANGUAGES
        self.locale = locale.lower()
        self.template_file_path = get_template_file_path(template_set_dir, self.locale)
        self._metadata = get_template_set_metadata(template_set_dir)
        self._template_base_name = template_set_dir.split(os.sep)[-1]

        if not ("alias" in self._metadata):
            raise TemplateError("Missing alias key in metadata")
        self.validate_alias(self._metadata['alias'])

        if (not "subject" in self._metadata):
            raise TemplateError("Missing subject key in metadata")
        self.validate_subjects(self._metadata['subject'])

    def validate_alias(self, alias):
        if not isinstance(alias, str):
            raise TemplateError("Alias must be a string")
        if len(alias) < 4:
            raise TemplateError("Alias must be at least 4 characters")
        if any([ch in alias for ch in string.whitespace]):
            raise TemplateError("Alias must not contain whitespace")

    def validate_subjects(self, subjects_dict):
        if not isinstance(subjects_dict, dict):
            raise TemplateError(f"Subjects dict must be a dictionary. {subjects_dict} is of type {type(subjects_dict)}")

        missing_locales = set(SUPPORTED_LANGUAGES) - set(subjects_dict.keys())
        if missing_locales:
            raise TemplateError(f"Missing email subjects for locales: {', '.join(missing_locales)}")
        def validate_subject(subject, locale):
            # Locale is used here only for clearer error reporting
            if not isinstance(subject, str):
                raise TemplateError(f"Subject ({locale}) must be a string. {subject} is of type {type(subject)}")

            if len(subject) < 6:
                raise TemplateError(f"Subject ({locale}) must be at least 6 characters. Not {subject}")

        for locale, subject in subjects_dict.items():
            validate_subject(subject, locale)


    @property
    def content(self):
        with open(self.template_file_path, 'r') as f:
            content = f.read()
        return content

    @property
    def metadata(self):
        return self._metadata

    @property
    def alias(self):
        return self.metadata['alias']

    @property
    def subject(self):
        return self.metadata['subject'][self.locale]

    @property
    def name(self):
        return f'{self._template_base_name.title()}_{self.locale}'


class EmailTemplateSet(object):

    def __init__(self, location_dir):
        assert os.path.isdir(location_dir), f"{location_dir} is not a directory"
        self.location_dir = location_dir

    @property
    def template_base_name(self):
        return self.location_dir.split(os.sep)[-1]

    def get_all_templates(self):
        for locale in SUPPORTED_LANGUAGES:
            yield EmailTemplate(self.location_dir, locale)

    @staticmethod
    def template_base_name_from_template_set_dir(template_set_dir):
        template_base_name = template_set_dir.split(os.sep)[-1]
        return template_base_name


def prettify_payload(payload):
    def replace_keys_with_content_length(d, keys):
        assert isinstance(d, dict)
        assert isinstance(keys, list)
        for key in keys:
            try:
                d[key] = f"Content with length: {len(d[key])}"
            except KeyError:
                pass
    out = copy(payload)
    replace_keys_with_content_length(out, ['HtmlBody', 'TextBody'])
    return out



class EmailTemplateManager(object):

    def __init__(self, email_templates_base_dir, limit_locale=None, limit_template_set=None):
        self.limit_locale = limit_locale
        self.rs = requests.Session()
        # from unittest.mock import Mock
        # self.rs = Mock()
        self.template_cache = TemplateCache(self.rs)
        candidate_paths = [os.path.join(email_templates_base_dir, file_or_dir) for file_or_dir in os.listdir(email_templates_base_dir)]
        template_dirs = [candidate for candidate in candidate_paths if os.path.isdir(candidate)]
        self.email_template_sets = [EmailTemplateSet(dir_) for dir_ in template_dirs]
        if limit_template_set:
            self.email_template_sets = [ts for ts in self.email_template_sets
                                        if ts.template_base_name == limit_template_set]
        cfg = get_settings()
        self.rs.headers.update({'X-Postmark-Server-Token': cfg['POSTMARK_SERVER_TOKEN']})
        print(f"Initialised eml_template_mgr. With template_dirs\n{template_dirs}")

    def upload_templates(self):
        for template_set in self.email_template_sets:
            print(f"Uploading template_set for {template_set.template_base_name}")
            for template in template_set.get_all_templates():
                if self.limit_locale and template.locale != self.limit_locale:
                    continue
                self.upsert_template(template.alias, template.name, template.subject, template.content)

    def _update_template(self, template_alias, template_name, subject, html_body, text_body=None):
        url = BASE_URL + f'/templates/{template_alias}'
        payload = {
              "Name": template_name,
              "Subject": subject,
              "Alias": template_alias,
              "HtmlBody": html_body,
          }
        if text_body:
            payload['TextBody'] = text_body
        rich_print(f"[yellow]Updating template:[/yellow]\n {prettify_payload(payload)}")
        resp = self.rs.put(url, json=payload)
        data = resp.json()

        return data

    def _create_template(self, template_alias, template_name, subject, html_body, text_body=None):
        url = BASE_URL + f'/templates'
        payload = {
              "Name": template_name,
              "Subject": subject,
              "Alias": template_alias,
              "HtmlBody": html_body,
          }
        if text_body:
            payload['TextBody'] = text_body

        rich_print(f"[green]Creating template:[/green]\n {prettify_payload(payload)}")
        resp = self.rs.post(url, json=payload)
        data = resp.json()

        return data

    def upsert_template(self, template_alias, template_name, subject, html_body, text_body=None):
        rich_print(f"Sending template [blue]{template_name}[/blue] to postmark")
        template_exists = True
        try:
            self.template_cache.by_alias(template_alias)
        except TemplateNotFound:
            template_exists = False

        if template_exists:
            template = self._update_template(template_alias, template_name, subject, html_body, text_body)
        else:
            template = self._create_template(template_alias, template_name, subject, html_body, text_body)

        return template

@click.command()
@click.option('--limit-lang', default=None, help='Limit by language')
@click.option('--limit-template-set', default=None, help='Limit by template set')
@click.option('--everything', is_flag=True, help='Upload all templates')
def push_templates(limit_lang, limit_template_set, everything):
    if (limit_lang or limit_template_set) and everything:
        raise click.UsageError("The option --all and --limit options are mutually exclusive")
    if everything:
        click.confirm("Do you want to upload all email templates?", abort=True)
    mgr = EmailTemplateManager(EMAIL_TEMPLATES_BASE_DIR, limit_locale=limit_lang, limit_template_set=limit_template_set)
    mgr.upload_templates()


if __name__ == '__main__':
    push_templates()
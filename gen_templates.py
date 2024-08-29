import os

from jinja2 import Environment, FileSystemLoader
from babel.support import Translations

from cfg import SUPPORTED_LANGUAGES

BLUEPRINTS_DIR = 'template_blueprints'
OUTPUT_TEMPLATES_DIR = 'email_templates'
TRANSLATIONS_DIR = 'translations/'
VALID_FILENAME_EXTENSIONS = ('.html.j2', '.hbs.j2', '.html')

MISSING_TRANSLATION_PREFIX = 'XXX_MISSING_TRANS_XXX'

translations = None

MISSING_TRANSLATION_PREFIX = 'XXX_MISSING_TRANS_XXX'

translations = None

def is_valid_template_file(filename):
    for ext in VALID_FILENAME_EXTENSIONS:
        if filename.endswith(ext):
            return True
    return False

def mkdir_p(path):
    """Make a dir and return silently if it exists. Essentially mkdir -p path"""
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    return path

def render_blueprints(env: Environment, blueprint_fn, template_vars: dict):
    file_base_name = blueprint_fn.split('.')[0]
    template = env.get_template(blueprint_fn)

    def missing_translation_reporter(message):
        '''
        Prints out a standard message when no translation is found for `message`
        '''
        translated_message = translations.gettext(message)
        if translated_message == message:  # No translation found
            return f'{MISSING_TRANSLATION_PREFIX}: {message}'
        return translated_message

    for lang in SUPPORTED_LANGUAGES:
        global translations
        translations = Translations.load(TRANSLATIONS_DIR, [lang])
        env.install_gettext_translations(translations)
        # Override the _() function in the environment to use the custom one that reports missing trans
        env.globals['_'] = missing_translation_reporter

        outdir = mkdir_p(os.path.join(OUTPUT_TEMPLATES_DIR, file_base_name))
        outfile_name = os.path.join(outdir, f'{file_base_name}_{lang}.html')
        with open(outfile_name, mode='w', encoding='utf-8') as f:
            f.write(template.render(**template_vars))


# translations = {l: Translations.load(TRANSLATIONS_DIR, l) for l in SUPPORTED_LANGUAGES}

jinja_extensions = ['jinja2.ext.i18n']
jinja_env = Environment(loader=FileSystemLoader(f"{BLUEPRINTS_DIR}/"), extensions=jinja_extensions)


blueprint_filenames = [fn for fn in os.listdir(BLUEPRINTS_DIR) if is_valid_template_file(fn)]

for blueprint_filename in blueprint_filenames:
    render_blueprints(jinja_env, blueprint_filename, {})

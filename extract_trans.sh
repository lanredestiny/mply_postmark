pybabel extract -F babel_eml.cfg --sort-by-file --project=MULTIPLY_EMAILS --copyright-holder=Multiply -o translations/messages_eml.pot template_blueprints/** template_blueprints** template_blueprints/includes/**

python translized_push.py
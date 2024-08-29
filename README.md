# MULTIPLY email template builder
This tool will build Multiply's email templates in multiple languages. 
Very helpful instructions for using it will be added here in due course
This documentation assumes that you are using a Linux system.

## Setting yourself up
`source setup_project.sh` - Installs major requirements and leaves you inside a python virtual environment

## Email building Workflow
Do these once when you first work on this project
* Go to your repo location `cdpostmark`
* Install python dependencies `pip install -r requirements.txt`
* Create a config file `cp config.toml /home/$USER/cfg/mply_eml_config.toml` with your secrets
* Populate this config file with relevant values (these are secret) `nano $MPLY_EML_CONFIG`

Do these whenever you make a change to a template_blueprint
* Create your template_blueprints in `template_blueprints/`
* Run `./generate_templates.sh`. Before doing this ensure you have:
  * Exported your settings config file. `export MPLY_EML_CONFIG = /path/to/cfg.py`
  * Named all your template files with `html.j2` extensions e.g. `welcome_email.html.j2`
* Your generated templates should appear in `email_templates/` (check them out)
* Run `./upload_email_templates.sh` to upload these templates to Postmark (TODO: Needs to be implemented)

## Translation Workflow
* `./extract_trans.sh` will extract translatable strings and push them to the 
[Translized](https://app.translized.com) project
* Go to Translized and translate any untranslated keys (done by Multiply staff) 
* Run `./build_trans.sh` to pull key translations to your local machine

## Pushing everything to Postmark
After you have generated your templates, use `./upload_email_templates.sh` to upload all the generated 
templates to Postmark. You can go there and view them.

Note that this command will update any pre-existing template and create templates that don't exist. The way
to edit a template is to edit it locally then push changes to Postmark

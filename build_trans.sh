set -e

python translized_pull.py
pybabel compile -d translations/

#!/bin/bash -xe

export DJANGO_SETTINGS_MODULE=autoperry.production_settings

. venv/bin/activate

pip install -r production-requirements.txt

git pull

cd autoperry

./manage.py collectstatic --no-input
./manage.py migrate

systemctl --user restart autoperry


#!/bin/bash -xe

export DJANGO_SETTINGS_MODULE=autoperry.production_settings

. venv/bin/activate

git pull

pip install -r production-requirements.txt

cd autoperry

./manage.py collectstatic --no-input
./manage.py migrate

systemctl --user restart autoperry


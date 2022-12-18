#!/bin/bash

homedir="${HOME}/practice-night-support/"
appdir='autoperry'
app='autoperry.wsgi'
socket="unix:${HOME}/www/autoperry.cambridgeringing.info/proxy.sock"

cd ${homedir}

source venv/bin/activate

cd "${appdir}"
export DJANGO_SETTINGS_MODULE=autoperry.production_settings

gunicorn -b "${socket}" "${app}"



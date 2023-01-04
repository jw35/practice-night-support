#!/bin/bash

homedir="${HOME}/practice-night-support/"
appdir='autoperry'
log="${homedir}logs/send_helper_reminders.log"

cd ${homedir}

source venv/bin/activate

cd "${appdir}"
export DJANGO_SETTINGS_MODULE=autoperry.production_settings

echo "*** Running $(date)" >>"${log}"

./manage.py send_helper_reminders --really >>"${log}"




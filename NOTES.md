# AutoPerry - Notes

Activate Python environment with: `. venv/bin/activate`

Dummy SMTP server for development: `python -m smtpd -n -c DebuggingServer localhost:1025` (no longer needed)

Development server on http://127.0.0.1:8000/: `cd autoperry/; ./manage.py runserver`

Installed in ~/practice-night-support on caracal.

Create, activate and populate Python virtual environment with:

    cd ~/practice-night-support
    python3 -mvenv venv
    . venv/bin/activate 
    pip install -r production-requirements.txt

Set the web server to proxy to Gunicorn:

    touch ~/www/autoperry.cambridgeringing.info/.proxy-to-socket

The script run_autoperry.sh will start up the app under Gunicorn interactively using settings from `~/practice-night-support/autoperry/autoperry/production_settings.py`

Copy the systemd unit file `autoperry.service` to ~/.config/systemd/user

To start:

    systemctl --user daemon-reload
    systemctl --user start autoperry

To stop 

    systemctl --user stop autoperry

To restart

    systemctl --user restart autoperry

To make persistent

    systemctl --user enable autoperry

To view logs

    journalctl --user

Cronjobs to send reminders:

    crontab -e

and add

    00 05 * * * practice-night-support/run_backup.sh
    00 06 * * * practice-night-support/run_owner_reminders.sh
    00 07 * * 7 practice-night-support/run_helper_reminders.sh
    05 07 * * 7 practice-night-support/run_advert.sh
    00 08 * * * practice-night-support/run_admin_reminders.sh

## Deploying a new version

    export DJANGO_SETTINGS_MODULE=autoperry.production_settings
    cd ~/practice-night-support
    . venv/bin/activate
    systemctl --user stop autoperry
    git pull
    cd autoperry
    ./manage.py collectstatic
    ./manage.py migrate
    systemctl --user start autoperry
#!/bin/bash

homedir="${HOME}/practice-night-support/"

# Mon,Tue, etc
dow=$(date +%a)

file="backups/backup-${dow}"
if [ "${dow}" = "Sun" ]
then
    file="backups/backup-$(date +%b)"
fi

cd "${homedir}"

mysqldump --defaults-extra-file=backup_params jonw > "${file}"


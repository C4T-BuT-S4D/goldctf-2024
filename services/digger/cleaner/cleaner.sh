#!/bin/sh

while true; do
    date -uR

    find "/var/digger/storage/passwords/" \
        -type f \
        -and -not -newermt "-3600 seconds" \
        -delete

    find "/var/digger/storage/secrets/" \
        -type f \
        -and -not -newermt "-3600 seconds" \
        -delete

    sleep 60
done

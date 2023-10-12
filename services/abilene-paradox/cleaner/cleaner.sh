#!/usr/bin/env bash

while true; do
    find /cache -mindepth 1 -maxdepth 1 -type d -not -newermt '2 mins ago' | xargs rm -rf;
    sleep 5;
done

#!/bin/sh

while true; do
    socat TCP-LISTEN:31337,reuseaddr,fork SYSTEM:"timeout -s SIGKILL 60 ./digger"
done

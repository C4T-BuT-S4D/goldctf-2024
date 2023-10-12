#!/usr/bin/env bash

seq 1337 2360 | parallel -j 1024 -k /run_gotty.sh

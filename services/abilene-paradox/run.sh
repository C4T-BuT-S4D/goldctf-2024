#!/usr/bin/env bash

seq 14141 14652 | parallel -j 512 -k /run_gotty.sh

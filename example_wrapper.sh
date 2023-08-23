#!/bin/bash
"$HOME"/miniconda3/envs/gsay/bin/python "$HOME"/projects/gsay/main.py "$@" &
# We want to pass the termination signal to gsay, such that we can use `kill -SIGTERM gsay`
trap "kill -SIGTERM $!" SIGTERM
wait
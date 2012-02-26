#!/bin/sh
until python daemon.py; do
    echo "The GP daemon aborted with exit code $?.  Respawning in 30 seconds..." >&2
    rm -rf ~/.picloud/datalogs/Simulation
    sleep 30
done

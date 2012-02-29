#!/bin/sh

# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

# Daemonisation wrapper for the daemon.py genetic programming task grabber and simulator.
# This script is intended to be run from a simulation servant machine at startup.

until python daemon.py; do
    echo "The GP daemon aborted with exit code $?.  Respawning in 30 seconds..." >&2
    rm -rf ~/.picloud/datalogs/Simulation
    sleep 30
done

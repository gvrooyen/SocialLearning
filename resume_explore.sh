#!/bin/sh

# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

kill -s CONT $(ps -u gvrooyen -f | grep explore_fitness\.py | cut -c11-14 | sort | head -n1)

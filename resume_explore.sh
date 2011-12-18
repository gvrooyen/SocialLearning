#!/bin/sh
kill -s CONT $(ps -u gvrooyen -f | grep explore_fitness\.py | cut -c11-14 | sort | head -n1)

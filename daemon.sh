#!/bin/sh
nohup python daemon.py > daemon.log 2> daemon.err &

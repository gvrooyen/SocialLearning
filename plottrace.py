# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

"""
Script to estimate the rate at which the simulator's estimate of an agent's fitness,
converges to its final value. This can be used to decide how many rounds to play during
a genetic programming generation.
"""

from matplotlib.pylab import *
import matplotlib.pyplot as plt
from numpy import *
import pymongo

connection = pymongo.Connection()
db = connection.SocialLearning
# db.authenticate('', '')
dbc = db.trace_payoffs

estimate = []

X = range(0,10000,100)

for (i, record) in enumerate(dbc.find(limit=100)):
    trace = 1. * array(record['trace'])
    trace /= trace[-1]
    trace = trace[0::100]
    trace = abs(trace - 1.)
    diff = zeros(100)
    diff[1:100] = trace[1:100] - trace[0:99]
    estimate.append(trace)

trace_mean = mean(estimate,0)
trace_std = std(estimate,0)

print size(X)
print size(trace_mean)
print size(trace_std)

plt.figure()
plt.errorbar(X,trace_mean,trace_std)
plt.figure()
plt.plot(diff)
show()

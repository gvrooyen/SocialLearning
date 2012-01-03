from matplotlib.pylab import *
import matplotlib.pyplot as plt
from numpy import *
import pymongo

connection = pymongo.Connection('enoch.dyndns-home.com')
db = connection.SocialLearning
db.authenticate('gvrooyen','ala+joen')
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

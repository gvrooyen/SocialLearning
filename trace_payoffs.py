import simulate
import pymongo
import sys
import datetime

AGENT = 'Reference'

if __name__ == '__main__':

    simulate.agent = __import__('agents.fitness.'+AGENT, fromlist=['*'])
    connection = pymongo.Connection()

    db = connection.SocialLearning
    collection = db.trace_payoffs

    print "Simulating",
    sys.stdout.flush()

    # We'll log traces to the database until this program is terminated
    while True:

        simulation = simulate.Simulate(N_rounds = 10000)

        trace = []

        for round in xrange(0,10000):
            simulation.step()
            trace.append(1. * simulation.total_payoff / (round+1.))

        record = {'agent_name': AGENT+'.py',
                  'timestamp': datetime.datetime.now(),
                  'trace': trace
                 }

        collection.insert(record)
        connection.fsync()

        print ".",
        sys.stdout.flush()

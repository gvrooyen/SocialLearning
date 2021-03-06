# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

"""
Variation of explore_fitness.py that specifically explores the integrated solution agent, BlueGenes.py.
"""

import fitness
import random
import ranges
import pymongo
import datetime

from math import exp, log

LOG_RANGES = False

def selectParameters(agent_name, explore_ranges):
    """
    Return a set of simulation parameters for the specified agent's next fitness exploration run.

    Currently, the parameters are just uniform random samples from the specified ranges. Cleverer algorithms are
    possible, e.g. by exploring sparsely sampled regions, or by giving greater preference to "interesting" regions
    where one or more partial derivatives are high.

    For now we explore the agent_name parameter. It will become useful once we need to do database lookups to determine
    "good" regions to explore.
    """

    result = {}

    for key, value in explore_ranges.iteritems():

        if value[0] == bool:
            if value[1] == None:
                result[key] = random.choice((True, False))
            else:
                result[key] = value[1]

        elif value[0] == int:
            result[key] = random.randint(value[1], value[2])

        elif value[0] == float:
            if LOG_RANGES and (value[1] > 0.0) and (value[2] > 0.0) and (value[2]/value[1] > 100.0):
                # For a range specification like (float, 0.001, 0.4), rather sample on an log-range
                result[key] = exp(random.uniform(log(value[1]), log(value[2])))
            else:
                # For a range specification like (float, 0.0, 0.5), sample on a uniform range
                result[key] = random.uniform(value[1], value[2])

        else:
            raise ValueError("Unsupported range specification: %s" % value[0])

    return result


if __name__ == '__main__':

    connection = pymongo.Connection()

    db = connection.SocialLearning
    collection = db.solution

    while True:

        # Do an import by string reference. The 'fromlist' argument is necessary because we are importing a submodule
        # from a package (otherwise only the empty 'fitness' module will be imported
        agent = __import__('agents.fitness.BlueGenes', fromlist=['*'])

        try:
            explore_ranges = agent.explore_ranges
        except AttributeError:
            explore_ranges = ranges.ParameterRange

        params = selectParameters('BlueGenes', explore_ranges)

        sample = fitness.fitness('agents.fitness.BlueGenes', params, 1000, 20)

        print(agent.__name__)
        print(params)
        print("FITNESS: %d" % sample.avg_payoff)
        print("ERRORS: %d/%d" % (sample.N_errors, sample.N_runs))

        # Lastly, pack the record for this simulation run in a way that can neatly be stored in the database

        record = {'agent_name': 'BlueGenes',
                  'timestamp': datetime.datetime.now(),
                  'fitness': sample.avg_payoff,
                  'avg_T_move': sample.avg_T_move,
                  'N_errors': sample.N_errors,
                  'N_runs': sample.N_runs
                 }

        # Prefix all parameters with 'param_'
        for (key, value) in params.iteritems():
            record['param_'+key] = value

        collection.insert(record)
        connection.fsync()


# -*- coding: iso-8859-15 -*-

import simulate
import agent
import random
import sys
import argparse
import logging
import multiprocessing
import traceback

from multiprocessing import Pool, Lock

DEFAULT_ITERATIONS = 100
DEFAULT_ROUNDS = 10000

global accumulated_payoff
global counter
global errors
global accumulated_move_time
global lock

lock = Lock()

def reduce(stats):
    global accumulated_payoff
    global counter
    global accumulated_move_time
    
    lock.acquire()
    accumulated_payoff += stats[0]
    counter += 1
    accumulated_move_time += stats[1]
    lock.release()

def run_simulation(id, rounds, seed):
    logger = logging.getLogger(__name__)
    sim_seed = int(seed) + id
    logger.debug("Simulation %d started" % id)
    simulation = simulate.Simulate(N_rounds = rounds, seed=sim_seed)
    try:
        simulation.run(silent_fail = True, seed=sim_seed)
        if simulation.exception:
            logger.error("Error in simulation %d with seed %X:" % (id, sim_seed))
            logger.error(simulation.exception)
        else:
            logger.debug("Simulation %d completed" % id)
        return (1.0*simulation.total_payoff/simulation.round,  simulation.move_timer.avg_time())
    except:
        logger.critical("Unhandled error in simulation %d" % id)
        (T,V,S) = sys.exc_info()
        logger.critical(T)
        logger.critical(V.message)
        logger.critical(traceback.format_tb(S))
        lock.acquire()
        errors += 1
        lock.release()
        return 0
        
        
def fitness(agent_path, strategy=None, iterations=DEFAULT_ITERATIONS, rounds=DEFAULT_ROUNDS, seed=None):
    """
    Measure the fitness of the agent script at the specified path.
    """
    
    # TODO: Refactor __main__ into this function
    
    logger = logging.getLogger(__name__)
    
    if strategy:
        agent.MOVE_STRATEGY = strategy
        
    global accumulated_move_time
    global accumulated_payoff
    global counter
    global errors
        
    accumulated_move_time = 0.0
    accumulated_payoff = 0
    counter = 0
    errors = 0
    
    if seed == None:
        seed = random.getrandbits(32)
    random.seed(seed)
        
    pool = Pool()
    
    logger.info("Starting simulation of '%s' with seed: %s" % (strategy, seed))
    
    for i in xrange(0, iterations):
        logger.debug("Iteration %d" % (i, ))
        pool.apply_async(run_simulation, (i, rounds, seed), callback=reduce)
    
    pool.close()
    pool.join()
    
    logger.info("Processed %d runs, with %d errors." % (counter, errors))
    logger.info("Average move time: %.2f us" % (1e6 * accumulated_move_time / counter))
    logger.info("Average payoff per round: %.2f" % (1.0*accumulated_payoff/iterations))
        
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate the fitness of a social learning strategy")
    parser.add_argument('strategy', type=str, help="The name of the strategy to evaluate")
    parser.add_argument('-N', '--iterations', type=int, default=DEFAULT_ITERATIONS,
                        help="The number of iterations over which to estimate")
    parser.add_argument('-D', '--debug', type=bool, default = False,
                        help="Switch on debugging output")
    parser.add_argument('-R', '--rounds', type=int, default=DEFAULT_ROUNDS,
                        help="The number of rounds in each simulation")
    parser.add_argument('-S', '--seed', type=str, default = str(random.getrandbits(32)),
                        help="Random number seed (a hexadecimal integer) for the simulation")
    args = parser.parse_args()
                        
    if args.debug:
        logger = multiprocessing.log_to_stderr()
        logger.setLevel(multiprocessing.SUBDEBUG)
    
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)
    
    #agent.MOVE_STRATEGY = args.strategy
    #accumulated_payoff = 0
    #accumulated_move_time = 0.0
    #counter = 0
    #errors = 0
    #
    #seed = int(args.seed, 16)
    #random.seed(seed)
    #
    #pool = Pool()
    #
    #print("Starting simulation of '%s' with seed: %X" % (args.strategy, seed))
    #
    #for i in xrange(0, args.iterations):
        #pool.apply_async(run_simulation, (i,args.rounds), callback=reduce)

    #pool.close()
    #pool.join()

    #print("\n\nProcessed %d runs, with %d errors." % (counter, errors))
    #print("Average move time: %.2f us" % (1e6 * accumulated_move_time / counter))

    #print("Average payoff per round: %.2f" % (1.0*accumulated_payoff/args.iterations))

    fitness('agents/fitness/', args.strategy, args.iterations, args.rounds, args.seed)

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

def run_simulation(id,rounds):
    sim_seed = random.getrandbits(32)
    lock.acquire()
    print ("+%d" % id),
    sys.stdout.flush()  
    lock.release()
    simulation = simulate.Simulate(N_rounds = rounds)
    try:
        simulation.run(silent_fail = True, seed=sim_seed)
        lock.acquire()
        if simulation.exception:
            print ("!%d" % id),
            print >> sys.stderr, "\nError in simulation %d with seed %X:\n" % (id, sim_seed)
            print >> sys.stderr, simulation.exception
        else:
            print ("-%d" % id),
        sys.stdout.flush()
        sys.stderr.flush()
        lock.release()
        return (1.0*simulation.total_payoff/simulation.round,  simulation.move_timer.avg_time())
    except:
        lock.acquire()
        print("\nUnhandled error in simulation %d" % id)
        (T,V,S) = sys.exc_info()
        print(T, V.message)
        traceback.print_tb(S)
        errors += 1
        lock.release()
        return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate the fitness of a social learning strategy")
    parser.add_argument('strategy', type=str, help="The name of the strategy to evaluate")
    parser.add_argument('-N', '--iterations', type=int, default=100,
                        help="The number of iterations over which to estimate")
    parser.add_argument('-D', '--debug', type=bool, default = False,
                        help="Switch on debugging output")
    parser.add_argument('-R', '--rounds', type=int, default=10000,
                        help="The number of rounds in each simulation")
    parser.add_argument('-S', '--seed', type=str, default = str(random.getrandbits(32)),
                        help="Random number seed (a hexadecimal integer) for the simulation")
    args = parser.parse_args()
                        
    if args.debug:
        logger = multiprocessing.log_to_stderr()
        logger.setLevel(multiprocessing.SUBDEBUG)
    
    agent.MOVE_STRATEGY = args.strategy
    accumulated_payoff = 0
    accumulated_move_time = 0.0
    counter = 0
    errors = 0
    
    seed = int(args.seed, 16)
    random.seed(seed)
    
    pool = Pool()
    
    print("Starting simulation of '%s' with seed: %X" % (args.strategy, seed))
    
    for i in xrange(0, args.iterations):
        pool.apply_async(run_simulation, (i,args.rounds), callback=reduce)
        
    pool.close()
    pool.join()

    print("\n\nProcessed %d runs, with %d errors." % (counter, errors))
    print("Average move time: %.2f us" % (1e6 * accumulated_move_time / counter))

    print("Average payoff per round: %.2f" % (1.0*accumulated_payoff/args.iterations))

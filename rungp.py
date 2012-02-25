import solegene
import argparse
import simulate
import logging
import pprint
import pymongo
import gc
import datetime
import cPickle as pickle

def rungpy(d = 'default', n = 100, cloud = False, multiproc = False, debug = False, mode_spatial = False,
		   mode_cumulative = False, mode_model_bias = False, N_observe = 3, P_c = 0.001, P_copyFail = 0.1,
		   N_migrate = 5, r_max = 100):

	logger = logging.getLogger(__name__)
	logger.addHandler(logging.StreamHandler())
	logging.getLogger('solegene').addHandler(logging.StreamHandler())
	
	if debug:
		logger.setLevel(logging.DEBUG)
		logging.getLogger('solegene').setLevel(logging.DEBUG)
	else:
		logger.setLevel(logging.INFO)
		logging.getLogger('solegene').setLevel(logging.INFO)

	sim_parameters = {}

	for param in ['mode_spatial', 'mode_cumulative', 'mode_model_bias', 'N_observe', 'P_c', 'P_copyFail', 'N_migrate', 'r_max']:
		sim_parameters[param] = locals()[param]

	logger.debug("Simulating with parameters:")
	logger.debug(pprint.pformat(sim_parameters))

	connection = pymongo.Connection('sl-master.dyndns-server.com')

	db = connection.SocialLearning
	db.authenticate('sociallearning', 'twasbrilligandtheslithytoves')

	coll_generations = db['gp_' + d]

	start_generation = 0

	last_run = coll_generations.find_one(sort=[('timestamp', pymongo.DESCENDING)])
	if last_run:
		logger.info("Resuming from last logged population")
		GP = solegene.Generation(sim_parameters=sim_parameters, use_cloud=cloud, empty=True)
		start_generation = last_run['generation'] + 1
		for genome_pickle in last_run['next_population']:
			GP.population.append(pickle.loads(str(genome_pickle)))
	else:
		logger.info("Initialising new population")
		GP = solegene.Generation(sim_parameters=sim_parameters, use_cloud=cloud)

#	for i in xrange(start_generation, args.n):
	if start_generation < n:
		i = start_generation
		logger.debug("======================================================================")
		logger.debug("GENERATION %d" % i)

		GP.step_fitness()

		GP.population.sort(reverse=True, key=lambda genome: 1.0 * genome.simulation.total_payoff)
		BOG = GP.population[0]
		fitness = 1.0 * BOG.simulation.total_payoff / BOG.simulation.round

		# Don't add the entire simulation dump to the database
		tmp_simulation = BOG.simulation
		BOG.simulation = None

		# Modules can't be pickled
		del(BOG.agent_module)

		# create a data structure to store the last generation in the database, so that it's always possible to resume
		# the simulation

		record = {}

		record['BOG'] = {'hash': BOG.code_hash,
						 'fitness': fitness,
						 'state': BOG.state,
						 'traits': [(t, BOG.traits[t].values()) for t in BOG.traits],
						 'parents': BOG.parents,
						 # 'code': BOG.render(),
						 'pickle': pickle.dumps(BOG)
					    }
		
		# We'll need the simulation data again to evolve
		BOG.simulation = tmp_simulation
		
		logger.debug("----------------------------------------------------------------------")
		logger.debug("Best-of-Generation %d: %s (fitness %2f)" % (i, BOG.code_hash, fitness))
		logger.debug(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . ")
		logger.debug("State graph:")
		logger.debug(pprint.pformat(BOG.state))
		logger.debug(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . ")
		logger.debug("Traits:")
		logger.debug(pprint.pformat([(t, BOG.traits[t].values()) for t in BOG.traits]))

		GP.step_evolve()

		record['next_population'] = []
		for (idx, g) in enumerate(GP.next_population):
			GP.next_population[idx].agent_module = None
			GP.next_population[idx].simulation = None
			record['next_population'].append(pickle.dumps(g))

		record['timestamp'] = datetime.datetime.now()

		record['generation'] = i
		record['sim_parameters'] = sim_parameters

		coll_generations.insert(record)
		
		GP.population = GP.next_population

		# logger.debug("----------------------------------------------------------------------")
		# logger.debug("Collecting garbage...")
		# n = gc.collect()
		# logger.debug("Unreachable objects: %d" % n)
		# logger.debug("Remaining garbage: %s" % pprint.pformat(gc.garbage))


if __name__ == '__main__':

	# From the command line, it's just possible to train at a specific set of parameters. For ranges, the
	# solegene.Generation() class should be manipulated directly by a service function.

	parser = argparse.ArgumentParser(description="Run a single generation of a SOLEGENE genetic program")

	parser.add_argument('-d', metavar='deme', type=str, default='default',
						help="The name of the genetic programming deme")
	parser.add_argument('-n', type=int, default=100,
						help="The maximum number of generations to process")

	group = parser.add_mutually_exclusive_group()
	group.add_argument('-c', '--cloud', action='store_true', default=False,
						help="Perform simulation on PiCloud")
	group.add_argument('-m', '--multiproc', action='store_true', default=False,
		                help="Enable multiprocessor support")

	parser.add_argument('-D', '--debug', action='store_true', default=False,
						help="Switch on debugging output")
	parser.add_argument('--mode_spatial', action='store_true', default=False,
						help="Simulate multiple demes")
	parser.add_argument('--mode_cumulative', action='store_true', default=False,
						help="Simulate the ability to refine acts")
	parser.add_argument('--mode_model_bias', action='store_true', default=False,
						help="Simulate the ability to decide who to observe")
	parser.add_argument('--N_observe', type=int, default=simulate.N_OBSERVE,
						help="Number of models to observe when --mode_model_bias is active")
	parser.add_argument('--P_c', type=float, default=simulate.P_C,
						help="Probability that an act's payoff changes (per round)")                        
	parser.add_argument('--P_copyFail', type=float, default=simulate.P_COPYFAIL,
						help="Probability that copying an act will fail")                        
	parser.add_argument('--N_migrate', type=int, default=simulate.N_MIGRATE,
						help="Number of agents that migrate demes each round when --mode_spatial is active")
	parser.add_argument('--r_max', type=int, default=simulate.R_MAX,
						help="Maximum refinement gain when --mode_cumulative is active")                        
	args = parser.parse_args()

	rungpy(d = args.d, n = args.n, cloud = args.cloud, multiproc = args.multiproc, debug = args.debug,
		   mode_spatial = args.mode_spatial, mode_cumulative = args.mode_cumulative,
		   mode_model_bias = args.mode_model_bias, N_observe = args.N_observe, P_c = args.P_c,
		   P_copyFail = args.P_copyFail, N_migrate = args.N_migrate, r_max = args.r_max)


import argparse
import pymongo
import random
import pprint

MASTER_SERVER = 'sl-master.dyndns-server.com'
MONGO_USER = 'sociallearning'
MONGO_PASSWORD = 'twasbrilligandtheslithytoves'

MAX_DEMES = 10

modes = ('ord', 'orD', 'oRd', 'oRD', 'Ord', 'OrD', 'ORd', 'ORD', 'ex_BFD', 'ex_CPD', 'ex_BTN')

def print_stats(db):
	coll_names = db.collection_names()

	result = {}

	for m in modes:
		result[m] = [0]*MAX_DEMES
		for subm in [c for c in coll_names if c.startswith('gp_ '+m)]:
			idx = int(subm[(4+len(m)):])
			if idx < MAX_DEMES:
				coll = db[subm]
				result[m][idx] = coll.count()

	pprint.pprint(result)


def print_champ(db, deme):
	"""
	Run through a specific deme (or all the demes for a given mode), and find the individual with the
	highest fitness.
	"""

	if deme in modes:
		# The user specified an entire mode, not just a single deme
		coll_list = ['gp_ ' + deme + str(i) for i in range(0, MAX_DEMES)]
	else:
		coll_list = ['gp_ ' + deme]

	champ = None
	fitness = -1
	champ_coll = None

	for coll_name in coll_list:
		coll = db[coll_name]
		for i in coll.find():
			if i['BOG']['fitness'] > fitness:
				champ = i
				champ_coll = coll_name
				fitness = i['BOG']['fitness']

	print("\nThe champion (fitness %.1f) lived in Generation %d of %s" % (fitness, champ['generation'], champ_coll))
	print("\nState graph:")
	pprint.pprint(champ['BOG']['state'])
	print("\nTraits:")
	pprint.pprint(champ['BOG']['traits'])


def print_fitness(db):
	"""
	Print the highest fitness discovered in each deme.
	"""
	coll_names = db.collection_names()

	result = {}

	for m in modes:
		result[m] = [0]*MAX_DEMES
		for subm in [c for c in coll_names if c.startswith('gp_ '+m)]:
			idx = int(subm[(4+len(m)):])
			if idx < MAX_DEMES:
				coll = db[subm]
				fitness = 0.0
				for i in coll.find():
					if i['BOG']['fitness'] > fitness:
						fitness = i['BOG']['fitness']
				result[m][idx] = fitness

	pprint.pprint(result)


def gather(db):
	"""
	Scan all demes (collections starting with 'gp_') that are larger than GENERATION_THRESHOLD, and
	copy their champions to the 'champions' collection. Each individual's original deme and generation,
	and his simulation parameters, are also recorded.
	"""

	coll_names = [c for c in db.collection_names() if c.startswith('gp_')]

	# Remove the old collection
	db.drop_collection('champions')

	for coll_name in coll_names:
		print("Processing %s..." % coll_name)
		coll = db[coll_name]
		fitness = -1.0
		champ = None
		for i in coll.find():
			if i['BOG']['fitness'] > fitness:
				champ = i
				champ_coll = coll_name
				fitness = i['BOG']['fitness']
		if champ:
			print("Champion found, fitness %.1f" % fitness)
			coll = db.champions
			bog = champ['BOG']
			bog['collection'] = champ_coll
			bog['generation'] = champ['generation']
			bog['sim_parameters'] = champ['sim_parameters']
			coll.insert(bog)


if __name__ == '__main__':

	parser = argparse.ArgumentParser(description="Monitor and manage the SocialLearning genetic programming database")

	parser.add_argument('command', choices=['stats', 'champ', 'fitness', 'gather'],
						help="Operation to perform.")
	parser.add_argument('-d', '--deme', type=str, default=None,
		help="Mode (e.g. 'orD') or deme (e.g. 'orD3') on which to run the command")

	args = parser.parse_args()

	connection = pymongo.Connection('sl-master.dyndns-server.com')
	db = connection.SocialLearning
	db.authenticate(MONGO_USER, MONGO_PASSWORD)

	if args.command == 'stats':
		print_stats(db)
	elif args.command == 'champ':
		if not args.deme:
			parser.error("The 'champ' command requires the -d/--deme argument to be specified.")
		print_champ(db, args.deme)
	elif args.command == 'fitness':
		print_fitness(db)
	elif args.command == 'gather':
		gather(db)
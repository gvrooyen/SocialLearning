import pymongo
import argparse

if __name__ == '__main__':

	# Display information about the best-of-generation individuals for the specified deme

	parser = argparse.ArgumentParser(description="Display information about the best-of-generation individuals for the specified deme")

	parser.add_argument('-d', metavar='deme', type=str, default='default',
						help="The name of the genetic programming deme")

	args = parser.parse_args()

	conn = pymongo.Connection()
	db = conn.SocialLearning
	coll = db['gp_' + args.d]

	for X in coll.find():
		print(X['generation'], X['BOG']['fitness'], X['BOG']['state'])

from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message
import boto
import json
import argparse
import pymongo

MASTER_SERVER = 'sl-master.dyndns-server.com'
MONGO_USER = 'sociallearning'
MONGO_PASSWORD = 'twasbrilligandtheslithytoves'
AWS_ACCESS = 'AKIAI7N2KZW6HMYE3QDQ'
AWS_SECRET = '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'


MAX_DEMES = 10
MAX_GENERATIONS = 30

modes = [
	('ord', []),
	('orD', ['--mode_spatial']),
	('oRd', ['--mode_cumulative']),
	('oRD', ['--mode_spatial', 'mode_cumulative']),
	('Ord', ['--mode_model_bias']),
	('OrD', ['--mode_model_bias', '--mode_spatial']),
	('ORd', ['--mode_model_bias', '--mode_cumulative']),
	('ORD', ['--mode_model_bias', '--mode_spatial', 'mode_cumulative'])
]

def assess_progress():
	"""
	Count the number of demes simulated for each mode, as well as the number of generations
	in each mode's final deme. Returns a dictionary in the following form:
	   dict[mode] = (number_of_demes, generations_in_last_deme)
	"""
	conn = pymongo.Connection(MASTER_SERVER)
	db = conn.SocialLearning
	db.authenticate(MONGO_USER, MONGO_PASSWORD)

	coll_names = db.collection_names()

	result = {}

	for m in modes:
		subm = [c for c in coll_names if c.startswith('gp_'+m[0])]

		cn = 'gp_' + m[0] + str(len(subm))
		coll = db[cn]

		result[m[0]] = (len(subm), coll.count())

	return result

conn = SQSConnection(AWS_ACCESS, AWS_SECRET)
task_queue = conn.get_queue('GP_tasks')

if task_queue.count() > 0:
	raise RuntimeError("There are still tasks to be processed.")

print("Current progress:")
pg = assess_progress()
print pg

for m in pg:
	for i in xrange(0, MAX_GENERATIONS-pg[m][1]):
		msg = Message()
		msg.set_body(json.dumps(['-d ' + m + str(pg[m][1])] + modes[m]))
		task_queue.write(msg)
	for i in xrange(m[0]+1, MAX_DEMES):
		msg = Message()
		msg.set_body(json.dumps(['-d ' + m + str(i)] + modes[m]))
		task_queue.write(msg)

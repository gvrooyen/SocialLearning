# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

"""
Command-line script used to post genetic programming simulation jobs to the AWS SQS queue, for later
consumption and execution by servant instances in the AWS EC2 cloud.
"""

from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message
import boto
import json
import argparse
import pymongo
import random

MASTER_SERVER = 'sl-master.dyndns-server.com'
MONGO_USER = 'sociallearning'
MONGO_PASSWORD = 'twasbrilligandtheslithytoves'
AWS_ACCESS = 'AKIAI7N2KZW6HMYE3QDQ'
AWS_SECRET = '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'


MAX_DEMES = 7
MAX_GENERATIONS = 40

modes = [
	('ord', []),
	('orD', ['--mode_spatial']),
	#('oRd', ['--mode_cumulative']),
	#('oRD', ['--mode_spatial', '--mode_cumulative']),
	('Ord', ['--mode_model_bias']),
	('OrD', ['--mode_model_bias', '--mode_spatial']),
	#('ORd', ['--mode_model_bias', '--mode_cumulative']),
	#('ORD', ['--mode_model_bias', '--mode_spatial', '--mode_cumulative']),
	#('ex_BFD', ['--mode_model_bias', '--mode_spatial', '--mode_cumulative', '--exemplar=BifurcateDiscrete']),
	#('ex_CPD', ['--mode_model_bias', '--mode_spatial', '--mode_cumulative', '--exemplar=ContinuousProfessionalDevelopment']),
	#('ex_BTN', ['--mode_model_bias', '--mode_spatial', '--mode_cumulative', '--exemplar=Beatnik']),
	#('ex_BIS', ['--mode_model_bias', '--mode_spatial', '--mode_cumulative', '--exemplar=BeatnikInSpace']),
	('ex_REF', ['--mode_spatial'])
]

def assess_progress():
	"""
	Count the number of demes simulated for each mode, as well as the number of generations
	in each mode's final deme. Returns a dictionary in the following form:
	   dict[mode] = [gen0, gen1, ...]
	"""
	conn = pymongo.Connection(MASTER_SERVER)
	db = conn.SocialLearning
	db.authenticate(MONGO_USER, MONGO_PASSWORD)

	coll_names = db.collection_names()

	result = {}

	for m in modes:
		result[m[0]] = [0]*MAX_DEMES
		for subm in [c for c in coll_names if c.startswith('gp_ '+m[0])]:
			idx = int(subm[4 + len(m[0]):])
			if idx < MAX_DEMES:
				coll = db[subm]
				result[m[0]][idx] = coll.count()

	return result

conn = SQSConnection(AWS_ACCESS, AWS_SECRET)
task_queue = conn.get_queue('GP_tasks')

print("Current progress:")
pg = assess_progress()
print pg

if task_queue.count() > 0:
	raise RuntimeError("There are still tasks to be processed.")

jobs = []

# The ideal execution order for tasks, is to fill up lower-order demes first, and to cycle
# through modes as much as possible to prevent servants from duplication generations
# (it's not wasted effort, but it's not ideal either)

# for n_bucket in xrange(0, MAX_DEMES):
# 	nothing_changed = False
# 	while not nothing_changed:
# 		nothing_changed = True
# 		for m in modes:
# 			if pg[m[0]][n_bucket] < MAX_GENERATIONS:
# 				print(m[0] + str(n_bucket))
# 				msg = Message()
# 				msg.set_body(json.dumps(['-d ' + m[0] + str(n_bucket)] + m[1]))
# 				jobs.append(msg)
# 				nothing_changed = False
# 				pg[m[0]][n_bucket] += 1

nothing_changed = False
while not nothing_changed:
	nothing_changed = True
	for n_bucket in xrange(0, MAX_DEMES):
		for m in modes:
			if pg[m[0]][n_bucket] < MAX_GENERATIONS:
				print(m[0] + str(n_bucket))
				msg = Message()
				msg.set_body(json.dumps(['-d ' + m[0] + str(n_bucket)] + m[1]))
				jobs.append(msg)
				nothing_changed = False
				pg[m[0]][n_bucket] += 1

# for (idx,m) in enumerate(pg):
# 	for i in xrange(0, MAX_GENERATIONS-pg[m][1]):
# 		msg = Message()
# 		msg.set_body(json.dumps(['-d ' + m + str(pg[m][1])] + modes[idx][1]))
# 		jobs.append(msg)
# 	for i in xrange(pg[m][0]+1, MAX_DEMES):
# 		msg = Message()
# 		msg.set_body(json.dumps(['-d ' + m + str(i)] + modes[idx][1]))
# 		jobs.append(msg)

# random.shuffle(jobs)

for m in jobs:
	task_queue.write(m)


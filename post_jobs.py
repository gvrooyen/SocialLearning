import boto
import json
import argparse
import pymongo

MASTER_SERVER = 'sl-master.dyndns-server.com'
MONGO_USER = 'sociallearning'
MONGO_PASSWORD = 'twasbrilligandtheslithytoves'

MAX_DEMES = 100
MAX_GENERATIONS = 30

demes = [
	'ord', [],
	'orD', ['--mode_spatial'],
	'oRd', ['--mode_cumulative'],
	''
]
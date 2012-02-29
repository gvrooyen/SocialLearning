# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

"""
Grab genetic programming tasks from the AWS SQS queue, and run the simulations.
This script is intended to be called from the command line.
"""

from boto.sqs.connection import SQSConnection
import logging
import subprocess
from datetime import datetime
import time
import os
import json

AWS_ACCESS = ''
AWS_SECRET = ''

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

def logformat(message):
	return "[%s %s] %s" % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),
				os.uname()[1], message)

conn = SQSConnection(AWS_ACCESS, AWS_SECRET)

task_queue = conn.get_queue('GP_tasks')

while True:

	while task_queue.count() > 0:
		# Give the machine two hours to complete this task before letting the message lapse back to the queue
		msg = task_queue.get_messages(visibility_timeout = 60*60*2)
		try:
			msg_body = msg[0].get_body()
			logger.info(logformat("Starting task: %s" % msg_body))
			args = json.loads(msg_body)
			output = subprocess.check_call(['python', '-OO', 'rungp.py', '-m'] + args)
		except subprocess.CalledProcessError:
			logger.error(logformat("Error executing task: %s" % msg_body))
		else:
			logger.info(logformat("Completed task: %s" % msg_body))
			task_queue.delete_message(msg[0])

		try:
			output = subprocess.check_call(['rm', '-rf', '~/.picloud/datalogs/Simulation'])
		except:
			logger.error(logformat("Could not remove picloud datalogs."))

	logger.info(logformat("Task queue is empty. Sleeping for 60 seconds before trying again."))
	time.sleep(60)

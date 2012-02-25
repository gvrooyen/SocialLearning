from boto.sqs.connection import SQSConnection
import logging
import subprocess
from datetime import datetime
import time
import os
import json

AWS_ACCESS = 'AKIAI7N2KZW6HMYE3QDQ'
AWS_SECRET = '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'

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

conn = SQSConnection(AWS_ACCESS, AWS_SECRET)

task_queue = conn.get_queue('GP_tasks')

while True:

	while task_queue.count() > 0:
		msg = task_queue.get_messages()
		try:
			msg_body = msg[0].get_body()
			print("[%s %s] Starting task: %s" % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),
				os.uname()[1], msg_body))
			args = json.loads(msg_body)
			output = subprocess.check_call(['python', '-OO', 'rungp.py', '-m'] + args)
		except subprocess.CalledProcessError:
			print("[%s %s] Error executing task: %s" % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),
				os.uname()[1], msg_body))
			# Repost the message so that someone else can try executing it
		else:
			print("[%s %s] Completed task: %s" % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),
				os.uname()[1], msg_body))
			task_queue.delete_message(msg)

	logger.info("[%s %s] Task queue is empty. Sleeping for 60 seconds before trying again." %
		(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), os.uname()[1]))
	time.sleep(60)

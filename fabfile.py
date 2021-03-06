# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

"""
Fabric utilities to do deployment and run commands across a group of (typically cloud-based)
servers.
"""

from fabric.api import *

env.roledefs = {
    'master': ['ec2-user@sl-master.dyndns-server.com'],
    'servant': ['ec2-user@ec2-184-73-138-89.compute-1.amazonaws.com',
                'ec2-user@ec2-107-22-12-215.compute-1.amazonaws.com',
                'ec2-user@ec2-184-72-65-151.compute-1.amazonaws.com',
                'ec2-user@ec2-184-72-137-158.compute-1.amazonaws.com',
				'ec2-user@ec2-50-17-1-67.compute-1.amazonaws.com',
				'ec2-user@ec2-72-44-53-225.compute-1.amazonaws.com',
				'ec2-user@ec2-107-22-142-165.compute-1.amazonaws.com',
				'ec2-user@ec2-107-22-53-205.compute-1.amazonaws.com',
				'ec2-user@ec2-23-20-67-140.compute-1.amazonaws.com',
				'ec2-user@ec2-107-22-63-205.compute-1.amazonaws.com',
				# 'ec2-user@ec2-184-72-79-114.compute-1.amazonaws.com',
				# 'ec2-user@ec2-107-20-117-21.compute-1.amazonaws.com',
				# 'ec2-user@ec2-50-16-35-89.compute-1.amazonaws.com',
				# 'ec2-user@ec2-50-16-162-62.compute-1.amazonaws.com',
				# 'ec2-user@ec2-50-17-104-123.compute-1.amazonaws.com',
				# 'ec2-user@ec2-174-129-130-158.compute-1.amazonaws.com',
				# 'ec2-user@ec2-23-20-29-2.compute-1.amazonaws.com',
				# 'ec2-user@ec2-23-20-16-14.compute-1.amazonaws.com'
                ]
}

@roles('servant')
@parallel
def check_load():
	"""
	Check the number of python processes currently running on the servant instances.
	"""

	run('ps -u ec2-user r -f | grep python | wc -l')

@roles('servant')
@parallel
def push_update():
	"""
	Let each servant instance pull the latest software update from git. Also, remove some
	temporary data logs.
	"""

	try:
		run('killall python')
	except:
		pass
	try:
		run('rm -rf ~/.picloud/datalogs/Simulation')
	except:
		pass
	with cd('~/devel/SocialLearning'):
		run('git pull')

@roles(['master', 'servant'])
def change_passphrase():
	"""
	Change the SSH passphrase on each server.
	"""

	run('ssh-keygen -p')

@roles('servant')
@parallel
def flush_logs():
	"""
	Clear up disk space used by the picloud logs.
	"""

	try:
		run('rm -rf ~/.picloud/datalogs/Simulation')
	except:
		pass

@roles(['master', 'servant'])
@parallel
def disk_usage():
	"""
	Display the disk space remaining on each server.
	"""

	run('df -h /')

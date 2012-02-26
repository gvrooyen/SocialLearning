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
				'ec2-user@ec2-107-22-63-205.compute-1.amazonaws.com'
                ]
}

@roles('servant')
@parallel
def check_load():
	run('ps -u ec2-user r -f | grep python | wc -l')

@roles('servant')
@parallel
def push_update():
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
	run('ssh-keygen -p')

@roles('servant')
@parallel
def flush_logs():
	try:
		run('rm -rf ~/.picloud/datalogs/Simulation')
	except:
		pass

@roles(['master', 'servant'])
@parallel
def disk_usage():
	run('df -h /')

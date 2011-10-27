import shlex

config = shlex.shlex('tasks.cfg')

print config.get_token()

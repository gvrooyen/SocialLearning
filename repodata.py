import git

class RepoData:

    def __init__(self):

        self.repo = git.Repo('.')
        assert self.repo.bare == False

        self.hc = self.repo.head.commit     # e.g. hc.hexsha is the commit's reference ID
        self.hct = self.hc.tree

        agent_blobs = [blob for blob in self.hct/"agents/fitness"
                                if blob.name.endswith('.py') and not blob.name.startswith('__')]

        # E.g. to print the SHA-1 identifiers of the agents whose fitness must be measured:
        #   [a[0].hexsha for a in r.agents_fitness]

        # Next, compile a list of agents with uncommitted changes in the working copy. These could be excluded when
        # doing simulations, since they are likely to still be "under construction". Also, since the hexsha of the
        # agent's blob in the git repository is saved with the simulation, we only ever want to work with agent modules
        # where the working copy (which will be imported into Python) is identical to the copy at the head of the
        # repository.

        diff = self.repo.index.diff(None)

        agent_diffs = [d.a_blob.name for d in diff if d.a_blob.path.startswith('agents/fitness/') and
        	d.a_blob.name.endswith('.py') and not d.a_blob.name.startswith('__')]

        self.agents_fitness = [(agent, (agent.name in agent_diffs)) for agent in agent_blobs]

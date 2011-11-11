import git

class RepoData:
    
    def __init__(self):
        
        self.repo = git.Repo('.')
        assert self.repo.bare == False
        
        self.hc = self.repo.head.commit     # e.g. hc.hexsha is the commit's reference ID
        self.hct = self.hc.tree
        
        self.agents_fitness = [blob for blob in self.hct/"agents/fitness" 
                               if (blob.name[-3:] == '.py') and (blob.name[0:2] != '__')]
                               
        # E.g. to print the SHA-1 identifiers of the agents whose fitness must be measured:
        #   [a.hexsha for a in r.agents_fitness]
